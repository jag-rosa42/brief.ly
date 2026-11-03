from uuid import uuid4

import pytest

from src.application.use_cases.get_current_profile import GetCurrentProfile
from src.domain.entities.profile import Profile
from src.domain.exception import ProfileNotFoundError
from tests.fakes import FakeProfileRepository


def test_execute_raises_when_profile_does_not_exist() -> None:
    profile_repository = FakeProfileRepository()
    use_case = GetCurrentProfile(
        profile_repository=profile_repository,
    )

    with pytest.raises(ProfileNotFoundError):
        use_case.execute(uuid4())


def test_execute_returns_the_stored_profile() -> None:
    profile = Profile.create(
        account_id=uuid4(), name="John", topic_ids=["science", "sports"]
    )
    profile_repository = FakeProfileRepository()
    profile_repository.add(profile)
    use_case = GetCurrentProfile(profile_repository)
    result = use_case.execute(profile.account_id)

    assert result.account_id == profile.account_id
    assert result.name == "John"
    assert result.topic_ids == frozenset(["science", "sports"])
