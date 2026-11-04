from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.entities import Topic, TopicSummary
from src.infrastructure.database.models import TopicModel, TopicSummaryModel
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


@pytest.mark.integration
def test_list_all_maps_persisted_summary_metadata(db_session: Session):
    summarized_at = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)
    topic_model = db_session.scalar(select(TopicModel).where(TopicModel.id == "science"))
    assert topic_model is not None
    topic_model.summary = TopicSummaryModel(
        topic_id="science",
        text="Science summary",
        summarized_at=summarized_at,
        llm_model="test-model",
    )
    db_session.flush()

    topics = SqlAlchemyTopicRepository(db_session).list_all()

    assert (
        Topic(
            id="science",
            summary=TopicSummary(
                text="Science summary",
                summarized_at=summarized_at,
                llm_model="test-model",
            ),
        )
        in topics
    )


@pytest.mark.integration
def test_exists_reports_whether_a_topic_is_persisted(db_session: Session):
    repository = SqlAlchemyTopicRepository(db_session)

    assert repository.exists("science")
    assert not repository.exists("unknown")
