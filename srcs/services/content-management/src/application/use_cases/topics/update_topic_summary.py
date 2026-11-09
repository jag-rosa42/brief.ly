from datetime import UTC, datetime

from src.application.port import UnitOfWork
from src.domain.entities import Topic, TopicSummary
from src.domain.exception import TopicNotFoundError
from src.domain.repositories import TopicRepository


class UpdateTopicSummary:
    def __init__(self, uow: UnitOfWork, repository: TopicRepository) -> None:
        self._uow = uow
        self._repository = repository

    def execute(
        self,
        topic_id: str,
        text: str,
        llm_model: str,
        generation_duration_ms: int,
    ) -> Topic:
        with self._uow:
            if self._repository.get_by_id(topic_id) is None:
                raise TopicNotFoundError(topic_id)

            summary = TopicSummary(
                text=text,
                summarized_at=datetime.now(UTC),
                llm_model=llm_model,
                generation_duration_ms=generation_duration_ms,
            )
            topic = self._repository.update_summary(topic_id, summary)
            if topic is None:
                raise TopicNotFoundError(topic_id)

            self._uow.flush()
            self._uow.commit()
            return topic
