from dataclasses import replace
from datetime import UTC

import pytest

from src.application.use_cases.topics import UpdateTopicSummary
from src.domain.entities import Topic, TopicSummary
from src.domain.exception import TopicNotFoundError
from tests.fixtures.unit_of_work import FakeUnitOfWork


class FakeTopicRepository:
    def __init__(self, topic: Topic | None) -> None:
        self.topic = topic
        self.update_count = 0

    def get_by_id(self, topic_id: str) -> Topic | None:
        if self.topic is not None and self.topic.id == topic_id:
            return self.topic
        return None

    def exists(self, topic_id: str) -> bool:
        return self.get_by_id(topic_id) is not None

    def list_all(self) -> list[Topic]:
        return [self.topic] if self.topic is not None else []

    def update_summary(self, topic_id: str, summary: TopicSummary) -> Topic | None:
        self.update_count += 1
        topic = self.get_by_id(topic_id)
        if topic is None:
            return None
        self.topic = replace(topic, summary=summary)
        return self.topic


def test_creates_and_replaces_summary_with_a_new_utc_timestamp(
    uow: FakeUnitOfWork,
) -> None:
    repository = FakeTopicRepository(Topic("science"))
    use_case = UpdateTopicSummary(uow, repository)

    first = use_case.execute("science", "First", "model-a", 500)
    second = use_case.execute("science", "Second", "model-b", 750)

    assert first.summary is not None
    assert second.summary is not None
    assert first.summary.text == "First"
    assert second.summary.text == "Second"
    assert second.summary.llm_model == "model-b"
    assert second.summary.generation_duration_ms == 750
    assert second.summary.summarized_at >= first.summary.summarized_at
    assert second.summary.summarized_at.tzinfo == UTC
    assert repository.update_count == 2
    assert uow.flush_count == 2
    assert uow.commit_count == 2


def test_unknown_topic_raises_without_writing(uow: FakeUnitOfWork) -> None:
    repository = FakeTopicRepository(None)

    with pytest.raises(TopicNotFoundError):
        UpdateTopicSummary(uow, repository).execute("unknown", "Summary", "model", 10)

    assert repository.update_count == 0
    assert uow.commit_count == 0


def test_persistence_failure_rolls_back(uow: FakeUnitOfWork) -> None:
    class FailingTopicRepository(FakeTopicRepository):
        def update_summary(self, topic_id: str, summary: TopicSummary) -> Topic | None:
            raise RuntimeError("persistence failed")

    repository = FailingTopicRepository(Topic("science"))
    with pytest.raises(RuntimeError, match="persistence failed"):
        UpdateTopicSummary(uow, repository).execute("science", "Summary", "model", 10)

    assert uow.commit_count == 0
    assert uow.rollback_count == 1
