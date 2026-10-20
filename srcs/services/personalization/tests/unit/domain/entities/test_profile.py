from uuid import UUID, uuid4

import pytest

from src.domain.entities.profile import Profile
from src.domain.exception import InvalidInterests, InvalidName


def _topic_ids(count: int) -> list[UUID]:
    return [uuid4() for _ in range(count)]


def _build_profile() -> Profile:
    return Profile.create(account_id=uuid4(), name="John", topic_ids=_topic_ids(2))


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


def test_create_builds_a_profile() -> None:
    account_id: UUID = uuid4()
    topic_ids: list[UUID] = _topic_ids(2)

    profile = Profile.create(account_id=account_id, name="John", topic_ids=topic_ids)

    assert profile.account_id == account_id
    assert profile.name == "John"
    assert profile.topic_ids == frozenset(topic_ids)


def test_create_trims_the_name() -> None:
    profile = Profile.create(account_id=uuid4(), name="  John  ", topic_ids=[uuid4()])

    assert profile.name == "John"


def test_create_rejects_blank_name() -> None:
    with pytest.raises(InvalidName):
        Profile.create(account_id=uuid4(), name="   ", topic_ids=[uuid4()])


def test_create_rejects_empty_name() -> None:
    with pytest.raises(InvalidName):
        Profile.create(account_id=uuid4(), name="", topic_ids=[uuid4()])


def test_create_accepts_name_of_50_characters() -> None:
    profile = Profile.create(account_id=uuid4(), name="a" * 50, topic_ids=[uuid4()])

    assert profile.name == "a" * 50


def test_create_rejects_name_of_51_characters() -> None:
    with pytest.raises(InvalidName):
        Profile.create(account_id=uuid4(), name="a" * 51, topic_ids=[uuid4()])


def test_create_rejects_no_topic() -> None:
    with pytest.raises(InvalidInterests):
        Profile.create(account_id=uuid4(), name="John", topic_ids=[])


def test_create_accepts_4_topics() -> None:
    profile = Profile.create(account_id=uuid4(), name="John", topic_ids=_topic_ids(4))

    assert len(profile.topic_ids) == 4


def test_create_rejects_5_topics() -> None:
    with pytest.raises(InvalidInterests):
        Profile.create(account_id=uuid4(), name="John", topic_ids=_topic_ids(5))


def test_create_rejects_duplicated_topics() -> None:
    topic_id: UUID = uuid4()

    with pytest.raises(InvalidInterests):
        Profile.create(account_id=uuid4(), name="John", topic_ids=[topic_id, topic_id])


# ---------------------------------------------------------------------------
# rename
# ---------------------------------------------------------------------------


def test_rename_replaces_and_trims_the_name() -> None:
    profile = _build_profile()

    profile.rename("  Jane ")

    assert profile.name == "Jane"


@pytest.mark.parametrize("invalid_name", ["", "   ", "a" * 51])
def test_rename_rejects_invalid_name_and_keeps_the_previous_one(
    invalid_name: str,
) -> None:
    profile = _build_profile()

    with pytest.raises(InvalidName):
        profile.rename(invalid_name)

    assert profile.name == "John"


# ---------------------------------------------------------------------------
# replace_interests
# ---------------------------------------------------------------------------


def test_replace_interests_replaces_all_topics() -> None:
    profile = _build_profile()
    new_topic_ids: list[UUID] = _topic_ids(3)

    profile.replace_interests(new_topic_ids)

    assert profile.topic_ids == frozenset(new_topic_ids)


@pytest.mark.parametrize("count", [0, 5])
def test_replace_interests_rejects_invalid_number_of_topics_and_keeps_the_previous_ones(
    count: int,
) -> None:
    profile = _build_profile()
    previous_topic_ids: frozenset[UUID] = profile.topic_ids

    with pytest.raises(InvalidInterests):
        profile.replace_interests(_topic_ids(count))

    assert profile.topic_ids == previous_topic_ids


def test_replace_interests_rejects_duplicated_topics() -> None:
    profile = _build_profile()
    topic_id: UUID = uuid4()

    with pytest.raises(InvalidInterests):
        profile.replace_interests([topic_id, topic_id])
