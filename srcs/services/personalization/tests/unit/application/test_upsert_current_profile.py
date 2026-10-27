from types import TracebackType
from uuid import UUID, uuid4

import pytest

from src.application.exceptions import TopicCatalogUnavailableError
from src.application.use_cases.upsert_current_profile import UpsertCurrentProfile
from src.domain.entities.profile import Profile
from src.domain.exception import (
    InvalidNameError,
    ProfileFieldsRequiredError,
    UnknownTopicsError,
)
from tests.fakes import FakeTopicCatalog

CATALOG = ["business", "health", "science", "sports"]


class FakeProfileRepository:
    def __init__(self) -> None:
        self.profiles: dict[UUID, Profile] = {}

    def upsert(self, profile: Profile) -> bool:
        created = profile.account_id not in self.profiles
        self.profiles[profile.account_id] = profile
        return created

    def find_by_id(self, account_id: UUID) -> Profile | None:
        return self.profiles.get(account_id)

    def find_by_id_for_update(self, account_id: UUID) -> Profile | None:
        return self.find_by_id(account_id)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.committed = False

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass


def test_execute_creates_the_profile_when_none_exists() -> None:
    uow, profiles, catalog = (
        FakeUnitOfWork(),
        FakeProfileRepository(),
        FakeTopicCatalog(CATALOG),
    )
    use_case = UpsertCurrentProfile(uow, profiles, catalog)
    account_id = uuid4()

    profile, created = use_case.execute(account_id, name="John", topic_ids=["science"])

    assert created is True
    assert profile.name == "John"
    assert profile.topic_ids == frozenset(["science"])
    assert uow.committed is True


def test_execute_requires_name() -> None:
    uow, profiles, catalog = (
        FakeUnitOfWork(),
        FakeProfileRepository(),
        FakeTopicCatalog(CATALOG),
    )
    use_case = UpsertCurrentProfile(uow, profiles, catalog)
    account_id = uuid4()

    with pytest.raises(ProfileFieldsRequiredError):
        use_case.execute(account_id, name=None, topic_ids=["science"])


def test_execute_requires_topic_ids() -> None:
    uow, profiles, catalog = (
        FakeUnitOfWork(),
        FakeProfileRepository(),
        FakeTopicCatalog(CATALOG),
    )
    use_case = UpsertCurrentProfile(uow, profiles, catalog)
    account_id = uuid4()

    with pytest.raises(ProfileFieldsRequiredError):
        use_case.execute(account_id, name="John", topic_ids=None)


def test_execute_updates_name() -> None:
    uow, profiles, catalog = (
        FakeUnitOfWork(),
        FakeProfileRepository(),
        FakeTopicCatalog(CATALOG),
    )
    use_case = UpsertCurrentProfile(uow, profiles, catalog)
    account_id = uuid4()

    profile = use_case.execute(account_id, name="John", topic_ids=["science"])
    profile, changed = use_case.execute(account_id, name="Jack", topic_ids=["science"])

    assert changed is False
    assert profile.name == "Jack"
    assert profile.topic_ids == frozenset(["science"])
    assert uow.committed is True


def test_execute_updates_topic_ids() -> None:
    uow, profiles, catalog = (
        FakeUnitOfWork(),
        FakeProfileRepository(),
        FakeTopicCatalog(CATALOG),
    )
    use_case = UpsertCurrentProfile(uow, profiles, catalog)
    account_id = uuid4()

    profile = use_case.execute(account_id, name="John", topic_ids=["science"])
    profile, changed = use_case.execute(account_id, name="John", topic_ids=["sports"])

    assert changed is False
    assert profile.name == "John"
    assert profile.topic_ids == frozenset(["sports"])
    assert uow.committed is True


def test_execute_raises_when_topic_ids_are_unknown() -> None:
    uow, profiles, catalog = (
        FakeUnitOfWork(),
        FakeProfileRepository(),
        FakeTopicCatalog(CATALOG),
    )
    use_case = UpsertCurrentProfile(uow, profiles, catalog)
    account_id = uuid4()

    with pytest.raises(UnknownTopicsError):
        use_case.execute(account_id, name="John", topic_ids=["unknown"])


def test_execute_propagates_catalog_unavailability() -> None:
    uow, profiles, catalog = (
        FakeUnitOfWork(),
        FakeProfileRepository(),
        FakeTopicCatalog(CATALOG, available=False),
    )
    use_case = UpsertCurrentProfile(uow, profiles, catalog)
    account_id = uuid4()

    with pytest.raises(TopicCatalogUnavailableError):
        use_case.execute(account_id, name="John", topic_ids=["science"])


def test_execute_rejects_invalid_name() -> None:
    uow, profiles, catalog = (
        FakeUnitOfWork(),
        FakeProfileRepository(),
        FakeTopicCatalog(CATALOG),
    )
    use_case = UpsertCurrentProfile(uow, profiles, catalog)
    account_id = uuid4()

    with pytest.raises(InvalidNameError):
        use_case.execute(account_id, name="", topic_ids=["science"])
