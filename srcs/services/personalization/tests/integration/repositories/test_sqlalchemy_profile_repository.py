from uuid import uuid4

from sqlalchemy.orm import Session

from src.domain.entities.profile import Profile
from src.infrastructure.database.repositories.sqlalchemy_profile_repository import (
    SqlAlchemyProfileRepository,
)


def test_upsert_creates_the_profile(db_session: Session) -> None:
    repository = SqlAlchemyProfileRepository(db_session)
    profile = Profile.create(
        account_id=uuid4(), name="John", topic_ids=["science", "health"]
    )

    created = repository.upsert(profile)

    assert created is True
    assert repository.find_by_id(profile.account_id) == profile


def test_find_by_id_returns_none_for_unknown_account(db_session: Session) -> None:
    repository = SqlAlchemyProfileRepository(db_session)

    assert repository.find_by_id(uuid4()) is None


def test_upsert_updates_an_existing_profile(db_session: Session) -> None:
    repository = SqlAlchemyProfileRepository(db_session)
    profile = Profile.create(
        account_id=uuid4(), name="John", topic_ids=["science", "health"]
    )
    created = repository.upsert(profile)
    profile.rename("Jane")
    profile.replace_interests(["sports"])
    created = repository.upsert(profile)
    assert created is False
    assert repository.find_by_id(profile.account_id) == profile


def test_upsert_does_not_touch_other_profiles(db_session: Session) -> None:
    repository = SqlAlchemyProfileRepository(db_session)
    profile = Profile.create(
        account_id=uuid4(), name="John", topic_ids=["science", "health"]
    )
    another_profile = Profile.create(
        account_id=uuid4(), name="Jane", topic_ids=["business", "technology"]
    )
    repository.upsert(profile)
    repository.upsert(another_profile)
    profile.replace_interests(["sports"])
    repository.upsert(profile)
    assert repository.find_by_id(another_profile.account_id) == another_profile


def test_find_by_id_returns_the_timestamps(db_session: Session) -> None:
    repository = SqlAlchemyProfileRepository(db_session)
    profile = Profile.create(account_id=uuid4(), name="John", topic_ids=["science"])
    repository.upsert(profile)

    result = repository.find_by_id(profile.account_id)

    assert result is not None
    assert result.created_at is not None
    assert result.updated_at is not None
