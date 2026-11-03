from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
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


def test_topic_can_hold_summary_metadata():
    summarized_at = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)

    topic = Topic(
        id="science",
        summary="Science summary",
        summarized_at=summarized_at,
        summary_llm_model="test-model",
    )

    assert topic.summary == "Science summary"
    assert topic.summarized_at == summarized_at
    assert topic.summary_llm_model == "test-model"
