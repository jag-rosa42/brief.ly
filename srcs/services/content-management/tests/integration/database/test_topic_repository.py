import pytest
from sqlalchemy.orm import Session

from src.domain.entities import Topic
from src.infrastructure.database.repositories import SqlAlchemyTopicRepository


@pytest.mark.integration
def test_list_all_returns_persisted_topics(db_session: Session):
    topics = SqlAlchemyTopicRepository(db_session).list_all()

    assert set(topics) == {
        Topic(id="business"),
        Topic(id="entertainment"),
        Topic(id="general"),
        Topic(id="health"),
        Topic(id="science"),
        Topic(id="sports"),
        Topic(id="technology"),
    }
