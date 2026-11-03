from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from shared_auth.testing import FakeTokenIssuer
from sqlalchemy.orm import Session

from src.domain.entities.profile import Profile
from src.domain.entities.saved_article import SavedArticle
from src.infrastructure.database.models.saved_article import (
    SavedArticle as SavedArticleModel,
)
from src.infrastructure.database.repositories.sqlalchemy_profile_repository import (
    SqlAlchemyProfileRepository,
)
from tests.fixtures.auth import AuthHeaders
from tests.routes import INTERNAL_ME_PROFILE


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


def test_get_my_internal_profile_returns_the_profile(
    client: TestClient,
    db_session: Session,
    auth_headers: AuthHeaders,
) -> None:
    profile = Profile.create(
        account_id=uuid4(), name="John", topic_ids=["technology", "business"]
    )
    SqlAlchemyProfileRepository(db_session).upsert(profile)

    response = client.get(INTERNAL_ME_PROFILE, headers=auth_headers(profile.account_id))

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "John"
    assert body["topic_ids"] == ["business", "technology"]
    assert body["account_id"] == str(profile.account_id)
    assert body["saved_article_ids"] == []


def test_get_returns_the_saved_article_ids_most_recent_first(
    client: TestClient,
    db_session: Session,
    auth_headers: AuthHeaders,
) -> None:
    account_id = uuid4()
    now = datetime.now(UTC)
    newer = _save_article(db_session, account_id, saved_at=now)
    older = _save_article(db_session, account_id, saved_at=now - timedelta(days=1))
    _save_article(db_session, uuid4(), saved_at=now)  # another account

    response = client.get(INTERNAL_ME_PROFILE, headers=auth_headers(account_id))

    assert response.status_code == 200
    assert response.json()["saved_article_ids"] == [
        str(newer.article_id),
        str(older.article_id),
    ]


def test_get_returns_404_when_the_profile_does_not_exist(
    client: TestClient,
    db_session: Session,
    auth_headers: AuthHeaders,
) -> None:
    response = client.get(INTERNAL_ME_PROFILE, headers=auth_headers(uuid4()))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFILE_NOT_FOUND"


def test_get_returns_401_without_a_token(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.get(INTERNAL_ME_PROFILE)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_get_accepts_a_forwarded_public_api_token(
    client: TestClient,
    db_session: Session,
    token_issuer: FakeTokenIssuer,
) -> None:
    account_id = uuid4()
    profile = Profile.create(
        account_id=account_id, name="John", topic_ids=["technology", "business"]
    )
    SqlAlchemyProfileRepository(db_session).upsert(profile)

    token = token_issuer.public_api_token(account_id, scopes=["read"])

    response = client.get(INTERNAL_ME_PROFILE, headers=token_issuer.bearer(token))

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "John"
    assert body["topic_ids"] == ["business", "technology"]
    assert body["account_id"] == str(profile.account_id)
