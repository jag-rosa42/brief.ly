from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from src.domain.entities import Topic, TopicSummary
from src.infrastructure.database.models.topic import TopicModel
from src.infrastructure.database.models.topic_summary import TopicSummaryModel


class SqlAlchemyTopicRepository:
    def __init__(self, session: Session):
        self._session: Session = session

    def exists(self, topic_id: str) -> bool:
        statement = select(TopicModel.id).where(TopicModel.id == topic_id)
        return self._session.scalar(statement) is not None

    def list_all(self):
        statement: Select[tuple[TopicModel]] = select(TopicModel)
        topic_list = []
        for topic_model in self._session.scalars(statement):
            topic_list.append(self._to_domain(topic_model))
        return topic_list

    def get_by_id(self, topic_id: str) -> Topic | None:
        topic = self._session.get(TopicModel, topic_id)
        return self._to_domain(topic) if topic is not None else None

    def update_summary(self, topic_id: str, summary: TopicSummary) -> Topic | None:
        topic = self._session.get(TopicModel, topic_id)
        if topic is None:
            return None
        if topic.summary is None:
            topic.summary = TopicSummaryModel(
                topic_id=topic_id,
                text=summary.text,
                summarized_at=summary.summarized_at,
                llm_model=summary.llm_model,
                generation_duration_ms=summary.generation_duration_ms,
            )
        else:
            topic.summary.text = summary.text
            topic.summary.summarized_at = summary.summarized_at
            topic.summary.llm_model = summary.llm_model
            topic.summary.generation_duration_ms = summary.generation_duration_ms
        return self._to_domain(topic)

    @staticmethod
    def _to_domain(topic_model: TopicModel) -> Topic:
        return Topic(
            id=topic_model.id,
            summary=(
                TopicSummary(
                    text=topic_model.summary.text,
                    summarized_at=topic_model.summary.summarized_at,
                    llm_model=topic_model.summary.llm_model,
                    generation_duration_ms=topic_model.summary.generation_duration_ms,
                )
                if topic_model.summary is not None
                else None
            ),
        )
