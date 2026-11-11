from uuid import uuid4

from src.application.use_cases.find_current_profile import FindCurrentProfile
from src.domain.entities.profile import Profile
from tests.fakes import FakeProfileRepository


def test_execute_returns_none_when_the_profile_does_not_exist() -> None:
    use_case = FindCurrentProfile(FakeProfileRepository())

    assert use_case.execute(uuid4()) is None


def test_execute_returns_the_stored_profile() -> None:
    profile = Profile.create(
        account_id=uuid4(), name="John", topic_ids=["science", "sports"]
    )
    profile_repository = FakeProfileRepository()
    profile_repository.add(profile)

    result = FindCurrentProfile(profile_repository).execute(profile.account_id)

    assert result is not None
    assert result.account_id == profile.account_id
    assert result.name == "John"
