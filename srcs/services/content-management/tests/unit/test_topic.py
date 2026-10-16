from dataclasses import FrozenInstanceError
from typing import Protocol, cast

import pytest

from src.domain.entities import Topic


class MutableTopic(Protocol):
    id: str


def test_topic_has_a_string_identifier():
    topic = Topic(id="science")

    assert topic.id == "science"


def test_topic_identifier_is_immutable():
    topic = Topic(id="science")
    mutable_topic = cast(MutableTopic, topic)

    with pytest.raises(FrozenInstanceError):
        mutable_topic.id = "health"
