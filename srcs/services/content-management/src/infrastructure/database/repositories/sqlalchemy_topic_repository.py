from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from src.domain.entities import Topic, TopicSummary
from src.infrastructure.database.models.topic import TopicModel


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

    @staticmethod
    def _to_domain(topic_model: TopicModel) -> Topic:
        return Topic(
            id=topic_model.id,
            summary=(
                TopicSummary(
                    text=topic_model.summary.text,
                    summarized_at=topic_model.summary.summarized_at,
                    llm_model=topic_model.summary.llm_model,
                )
                if topic_model.summary is not None
                else None
            ),
        )
