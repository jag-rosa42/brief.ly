from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from shared_errors import ErrorResponse
from sqlalchemy.orm import Session

from src.api.dependencies import ACCOUNT_ID_HEADER_NAME
from src.domain.entities.profile import Profile
from src.domain.entities.saved_article import SavedArticle
from src.infrastructure.database.models.saved_article import (
    SavedArticle as SavedArticleModel,
)
from src.infrastructure.database.repositories.sqlalchemy_profile_repository import (
    SqlAlchemyProfileRepository,
)
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


def test_list_returns_the_saved_articles(client: TestClient, db_session: Session) -> None:
    account_id = uuid4()
    older = _save_article(db_session, account_id, datetime(2026, 1, 1, tzinfo=UTC))
    newer = _save_article(db_session, account_id, datetime(2026, 1, 2, tzinfo=UTC))

    response = client.get(
        ME_SAVED_ARTICLES, headers={ACCOUNT_ID_HEADER_NAME: str(account_id)}
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["article_id"] for item in items] == [
        str(newer.article_id),
        str(older.article_id),
    ]
    assert items[0]["title"] == "Article"
    assert items[0]["summary"] is None
    assert "account_id" not in items[0]


def test_list_returns_an_empty_list_without_saved_articles(
    client: TestClient, db_session: Session
) -> None:
    account_id = uuid4()

    response = client.get(
        ME_SAVED_ARTICLES, headers={ACCOUNT_ID_HEADER_NAME: str(account_id)}
    )

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_list_returns_401_without_the_account_header(
    client: TestClient, db_session: Session
) -> None:
    response = client.get(ME_SAVED_ARTICLES, headers={})

    assert response.status_code == 401
    assert (
        ErrorResponse.model_validate(response.json()).error.code == "INVALID_ACCOUNT_ID"
    )


def test_delete_removes_the_saved_article(
    client: TestClient, db_session: Session
) -> None:
    account_id = uuid4()
    article: SavedArticle = _save_article(
        db_session, account_id, datetime(2026, 1, 1, tzinfo=UTC)
    )
    response = client.delete(
        me_saved_article(article.article_id),
        headers={ACCOUNT_ID_HEADER_NAME: str(account_id)},
    )

    assert response.status_code == 204
    response = client.get(
        ME_SAVED_ARTICLES, headers={ACCOUNT_ID_HEADER_NAME: str(account_id)}
    )

    assert response.json() == {"items": []}


def test_delete_returns_204_when_the_article_is_not_saved(
    client: TestClient, db_session: Session
) -> None:
    account_id = uuid4()
    response = client.delete(
        me_saved_article(uuid4()),
        headers={ACCOUNT_ID_HEADER_NAME: str(account_id)},
    )

    assert response.status_code == 204


def test_delete_returns_422_when_the_article_id_is_not_a_uuid(
    client: TestClient, db_session: Session
) -> None:
    account_id = uuid4()
    response = client.delete(
        f"{ME_SAVED_ARTICLES}/Bonjour",
        headers={ACCOUNT_ID_HEADER_NAME: str(account_id)},
    )

    assert response.status_code == 422
    assert ErrorResponse.model_validate(response.json()).error.code == "VALIDATION_ERROR"
