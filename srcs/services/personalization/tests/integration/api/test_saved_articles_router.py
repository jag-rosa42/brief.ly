from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from shared_auth.testing import FakeTokenIssuer
from shared_errors import ErrorResponse
from sqlalchemy.orm import Session

from src.api.dependencies.article_catalog import get_article_catalog
from src.domain.entities.article import Article
from src.domain.entities.profile import Profile
from src.domain.entities.saved_article import MAX_SAVED_ARTICLES, SavedArticle
from src.infrastructure.database.models.saved_article import (
    SavedArticle as SavedArticleModel,
)
from src.infrastructure.database.repositories.sqlalchemy_profile_repository import (
    SqlAlchemyProfileRepository,
)
from src.main import app
from tests.fakes import FakeArticleCatalog
from tests.fixtures.auth import AuthHeaders
from tests.routes import ME_SAVED_ARTICLES, me_saved_article


def _save_article(
    db_session: Session, account_id: UUID, saved_at: datetime
) -> SavedArticle:
    SqlAlchemyProfileRepository(db_session).upsert(
        Profile.create(account_id=account_id, name="John", topic_ids=["science"])
    )
    saved_article = SavedArticle(
        account_id=account_id,
        article_id=uuid4(),
        title="Article",
        source="Source",
        topic_id="science",
        summary=None,
        url="https://example.com/article",
        read_time_minutes=5,
        saved_at=saved_at,
    )
    db_session.add(SavedArticleModel(**saved_article.__dict__))
    db_session.flush()
    return saved_article


def test_list_returns_the_saved_articles(
    client: TestClient, db_session: Session, auth_headers: AuthHeaders
) -> None:
    account_id = uuid4()
    older = _save_article(db_session, account_id, datetime(2026, 1, 1, tzinfo=UTC))
    newer = _save_article(db_session, account_id, datetime(2026, 1, 2, tzinfo=UTC))

    response = client.get(ME_SAVED_ARTICLES, headers=auth_headers(account_id))

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["article_id"] for item in items] == [
        str(newer.article_id),
        str(older.article_id),
    ]
    assert items[0]["title"] == "Article"
    assert items[0]["publisher_name"] == "Source"
    assert "source" not in items[0]
    assert items[0]["summary"] is None
    assert "account_id" not in items[0]


def test_list_returns_an_empty_list_without_saved_articles(
    client: TestClient, db_session: Session, auth_headers: AuthHeaders
) -> None:
    account_id = uuid4()

    response = client.get(ME_SAVED_ARTICLES, headers=auth_headers(account_id))

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_list_returns_401_without_a_token(
    client: TestClient, db_session: Session
) -> None:
    response = client.get(ME_SAVED_ARTICLES, headers={})

    assert response.status_code == 401
    assert ErrorResponse.model_validate(response.json()).error.code == "INVALID_TOKEN"


def test_delete_removes_the_saved_article(
    client: TestClient, db_session: Session, auth_headers: AuthHeaders
) -> None:
    account_id = uuid4()
    article: SavedArticle = _save_article(
        db_session, account_id, datetime(2026, 1, 1, tzinfo=UTC)
    )
    response = client.delete(
        me_saved_article(article.article_id),
        headers=auth_headers(account_id),
    )

    assert response.status_code == 204
    response = client.get(ME_SAVED_ARTICLES, headers=auth_headers(account_id))

    assert response.json() == {"items": []}


def test_delete_returns_204_when_the_article_is_not_saved(
    client: TestClient, db_session: Session, auth_headers: AuthHeaders
) -> None:
    account_id = uuid4()
    response = client.delete(
        me_saved_article(uuid4()),
        headers=auth_headers(account_id),
    )

    assert response.status_code == 204


def test_delete_returns_422_when_the_article_id_is_not_a_uuid(
    client: TestClient, db_session: Session, auth_headers: AuthHeaders
) -> None:
    account_id = uuid4()
    response = client.delete(
        f"{ME_SAVED_ARTICLES}/Bonjour",
        headers=auth_headers(account_id),
    )

    assert response.status_code == 422
    assert ErrorResponse.model_validate(response.json()).error.code == "VALIDATION_ERROR"


def test_list_returns_401_when_the_token_is_expired(
    client: TestClient, token_issuer: FakeTokenIssuer, db_session: Session
) -> None:
    response = client.get(
        ME_SAVED_ARTICLES,
        headers=token_issuer.bearer(
            token_issuer.user_token(uuid4(), expires_in=timedelta(seconds=-1))
        ),
    )

    assert response.status_code == 401
    assert ErrorResponse.model_validate(response.json()).error.code == "TOKEN_EXPIRED"


# ---------------------------------------------------------------------------
# POST /me/saved-articles/{article_id}
# ---------------------------------------------------------------------------

ARTICLE = Article(
    article_id=uuid4(),
    title="Open-source models narrow the enterprise gap",
    source="TechDaily",
    topic_id="technology",
    summary=None,
    url="https://www.aitechdaily.com/",
    read_time_minutes=0,
)


@pytest.fixture
def article_catalog() -> Generator[FakeArticleCatalog]:
    catalog = FakeArticleCatalog([ARTICLE])
    app.dependency_overrides[get_article_catalog] = lambda: catalog
    try:
        yield catalog
    finally:
        app.dependency_overrides.pop(get_article_catalog, None)


def _create_profile(db_session: Session, account_id: UUID) -> None:
    SqlAlchemyProfileRepository(db_session).upsert(
        Profile.create(account_id=account_id, name="John", topic_ids=["science"])
    )


def test_save_returns_the_snapshot(
    client: TestClient,
    db_session: Session,
    article_catalog: FakeArticleCatalog,
    auth_headers: AuthHeaders,
) -> None:
    account_id = uuid4()
    _create_profile(db_session, account_id)

    response = client.post(
        me_saved_article(ARTICLE.article_id), headers=auth_headers(account_id)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["article_id"] == str(ARTICLE.article_id)
    assert body["publisher_name"] == "TechDaily"
    assert body["summary"] is None
    assert body["saved_at"] is not None
    listed = client.get(ME_SAVED_ARTICLES, headers=auth_headers(account_id)).json()
    assert [item["article_id"] for item in listed["items"]] == [str(ARTICLE.article_id)]


def test_save_returns_404_without_a_profile(
    client: TestClient, article_catalog: FakeArticleCatalog, auth_headers: AuthHeaders
) -> None:
    response = client.post(
        me_saved_article(ARTICLE.article_id), headers=auth_headers(uuid4())
    )

    assert response.status_code == 404
    assert ErrorResponse.model_validate(response.json()).error.code == "PROFILE_NOT_FOUND"


def test_save_returns_404_when_the_article_is_unknown(
    client: TestClient,
    db_session: Session,
    article_catalog: FakeArticleCatalog,
    auth_headers: AuthHeaders,
) -> None:
    account_id = uuid4()
    _create_profile(db_session, account_id)

    response = client.post(me_saved_article(uuid4()), headers=auth_headers(account_id))

    assert response.status_code == 404
    assert ErrorResponse.model_validate(response.json()).error.code == "ARTICLE_NOT_FOUND"


def test_save_returns_409_when_the_article_is_already_saved(
    client: TestClient,
    db_session: Session,
    article_catalog: FakeArticleCatalog,
    auth_headers: AuthHeaders,
) -> None:
    account_id = uuid4()
    _create_profile(db_session, account_id)
    client.post(me_saved_article(ARTICLE.article_id), headers=auth_headers(account_id))

    response = client.post(
        me_saved_article(ARTICLE.article_id), headers=auth_headers(account_id)
    )

    assert response.status_code == 409
    assert (
        ErrorResponse.model_validate(response.json()).error.code
        == "ARTICLE_ALREADY_SAVED"
    )


def test_save_returns_409_when_the_limit_is_reached(
    client: TestClient,
    db_session: Session,
    article_catalog: FakeArticleCatalog,
    auth_headers: AuthHeaders,
) -> None:
    account_id = uuid4()
    for _ in range(MAX_SAVED_ARTICLES):
        _save_article(db_session, account_id, datetime(2026, 1, 1, tzinfo=UTC))

    response = client.post(
        me_saved_article(ARTICLE.article_id), headers=auth_headers(account_id)
    )

    assert response.status_code == 409
    assert (
        ErrorResponse.model_validate(response.json()).error.code
        == "SAVED_ARTICLES_LIMIT_REACHED"
    )


def test_save_returns_422_when_the_article_id_is_not_a_uuid(
    client: TestClient, article_catalog: FakeArticleCatalog, auth_headers: AuthHeaders
) -> None:
    response = client.post(f"{ME_SAVED_ARTICLES}/Bonjour", headers=auth_headers(uuid4()))

    assert response.status_code == 422
    assert ErrorResponse.model_validate(response.json()).error.code == "VALIDATION_ERROR"


def test_save_returns_503_when_content_management_is_down(
    client: TestClient, db_session: Session, auth_headers: AuthHeaders
) -> None:
    account_id = uuid4()
    _create_profile(db_session, account_id)
    app.dependency_overrides[get_article_catalog] = lambda: FakeArticleCatalog(
        [ARTICLE], available=False
    )
    try:
        response = client.post(
            me_saved_article(ARTICLE.article_id), headers=auth_headers(account_id)
        )
    finally:
        app.dependency_overrides.pop(get_article_catalog, None)

    assert response.status_code == 503
    assert (
        ErrorResponse.model_validate(response.json()).error.code == "SERVICE_UNAVAILABLE"
    )


def test_save_returns_401_without_a_token(
    client: TestClient, article_catalog: FakeArticleCatalog
) -> None:
    response = client.post(me_saved_article(ARTICLE.article_id), headers={})

    assert response.status_code == 401
    assert ErrorResponse.model_validate(response.json()).error.code == "INVALID_TOKEN"
