from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from shared_auth.testing import FakeTokenIssuer
from shared_errors import ErrorResponse
from sqlalchemy.orm import Session

from src.domain.entities.profile import Profile
from src.infrastructure.database.repositories.sqlalchemy_profile_repository import (
    SqlAlchemyProfileRepository,
)
from tests.fixtures.auth import AuthHeaders
from tests.routes import ME_PROFILE


def test_get_my_profile_returns_the_profile(
    client: TestClient,
    db_session: Session,
    auth_headers: AuthHeaders,
) -> None:
    profile = Profile.create(
        account_id=uuid4(), name="John", topic_ids=["technology", "business"]
    )
    SqlAlchemyProfileRepository(db_session).upsert(profile)

    response = client.get(ME_PROFILE, headers=auth_headers(profile.account_id))

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "John"
    assert body["topic_ids"] == ["business", "technology"]
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


def test_get_my_profile_returns_null_when_profile_does_not_exist(
    client: TestClient,
    db_session: Session,
    auth_headers: AuthHeaders,
) -> None:
    # Right after sign-up: no profile yet. A 200, so Chrome's console stays
    # clean; the frontend shows the profile form.
    response = client.get(ME_PROFILE, headers=auth_headers(uuid4()))

    assert response.status_code == 200
    assert response.json() is None


def test_get_my_profile_returns_401_without_a_token(
    client: TestClient, db_session: Session
) -> None:
    response = client.get(ME_PROFILE)

    assert response.status_code == 401
    assert ErrorResponse.model_validate(response.json()).error.code == "INVALID_TOKEN"


def test_get_my_profile_returns_401_with_an_invalid_token(
    client: TestClient, db_session: Session
) -> None:
    response = client.get(ME_PROFILE, headers={"Authorization": "Bearer not-a-token"})

    assert response.status_code == 401
    assert ErrorResponse.model_validate(response.json()).error.code == "INVALID_TOKEN"


def test_get_my_profile_returns_401_when_the_token_is_expired(
    client: TestClient, token_issuer: FakeTokenIssuer, db_session: Session
) -> None:
    response = client.get(
        ME_PROFILE,
        headers=token_issuer.bearer(
            token_issuer.user_token(uuid4(), expires_in=timedelta(seconds=-1))
        ),
    )

    assert response.status_code == 401
    assert ErrorResponse.model_validate(response.json()).error.code == "TOKEN_EXPIRED"
