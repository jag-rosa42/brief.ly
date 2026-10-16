from typing import cast

from sqlalchemy import Table, create_engine
from sqlalchemy.orm import Session

from src.domain.entities import Topic
from src.infrastructure.database.models import TopicModel
from src.infrastructure.database.repositories import SqlAlchemyTopicRepository


def test_list_all_returns_persisted_topics():
    engine = create_engine("sqlite://")
    topic_table = cast(Table, TopicModel.__table__)
    topic_table.create(engine)

    with Session(engine) as session:
        session.add_all(
            [
                TopicModel(id="science"),
                TopicModel(id="health"),
            ]
        )
        session.commit()

        topics = SqlAlchemyTopicRepository(session).list_all()

    assert set(topics) == {
        Topic(id="science"),
        Topic(id="health"),
    }
