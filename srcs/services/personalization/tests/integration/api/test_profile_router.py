from uuid import uuid4

from fastapi.testclient import TestClient
from shared_errors import ErrorResponse
from sqlalchemy.orm import Session

from src.api.dependencies import ACCOUNT_ID_HEADER_NAME
from src.domain.entities.profile import Profile
from src.infrastructure.database.repositories.sqlalchemy_profile_repository import (
    SqlAlchemyProfileRepository,
)
from tests.routes import ME_PROFILE


def test_get_my_profile_returns_the_profile(
    client: TestClient, db_session: Session
) -> None:
    profile = Profile.create(
        account_id=uuid4(), name="John", topic_ids=["technology", "business"]
    )
    SqlAlchemyProfileRepository(db_session).upsert(profile)

    response = client.get(
        ME_PROFILE, headers={ACCOUNT_ID_HEADER_NAME: str(profile.account_id)}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "John"
    assert body["topic_ids"] == ["business", "technology"]
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


def test_get_my_profile_returns_404_when_profile_does_not_exist(
    client: TestClient, db_session: Session
) -> None:
    response = client.get(ME_PROFILE, headers={ACCOUNT_ID_HEADER_NAME: str(uuid4())})

    assert response.status_code == 404
    assert ErrorResponse.model_validate(response.json()).error.code == "PROFILE_NOT_FOUND"


def test_get_my_profile_returns_401_without_the_account_header(
    client: TestClient, db_session: Session
) -> None:
    response = client.get(ME_PROFILE)

    assert response.status_code == 401
    assert (
        ErrorResponse.model_validate(response.json()).error.code == "INVALID_ACCOUNT_ID"
    )


def test_get_my_profile_returns_401_when_the_account_header_is_not_a_uuid(
    client: TestClient, db_session: Session
) -> None:
    response = client.get(ME_PROFILE, headers={ACCOUNT_ID_HEADER_NAME: "not-a-uuid"})

    assert response.status_code == 401
    assert (
        ErrorResponse.model_validate(response.json()).error.code == "INVALID_ACCOUNT_ID"
    )
