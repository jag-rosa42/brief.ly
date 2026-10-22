from uuid import UUID, uuid4

import pytest

from src.application.use_cases.get_current_profile import GetCurrentProfile
from src.domain.entities.profile import Profile
from src.domain.exception import ProfileNotFoundError


class FakeProfileRepository:
    def __init__(self) -> None:
        self._profiles_by_id: dict[UUID, Profile] = {}

    def add(self, profile: Profile) -> None:
        self._profiles_by_id[profile.account_id] = profile

    def upsert(self, profile: Profile) -> bool:
        created = profile.account_id not in self._profiles_by_id
        self._profiles_by_id[profile.account_id] = profile
        return created

    def find_by_id(self, account_id: UUID) -> Profile | None:
        return self._profiles_by_id.get(account_id)


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
