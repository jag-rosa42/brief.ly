from uuid import uuid4

import pytest

from src.application.exceptions import TopicCatalogUnavailableError
from src.application.use_cases.upsert_current_profile import UpsertCurrentProfile
from src.domain.exception import (
    InvalidNameError,
    ProfileFieldsRequiredError,
    UnknownTopicsError,
)
from tests.fakes import FakeProfileRepository, FakeTopicCatalog, FakeUnitOfWork

CATALOG = ["business", "health", "science", "sports"]


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
