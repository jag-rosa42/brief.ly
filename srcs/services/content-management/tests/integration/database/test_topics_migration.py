from uuid import uuid4

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.infrastructure.database.models import SourceModel, TopicModel

INITIAL_TOPIC_IDS = {
    "business",
    "entertainment",
    "general",
    "health",
    "science",
    "sports",
    "technology",
}


@pytest.mark.integration
def test_migration_creates_and_seeds_the_topics_table(db_session: Session):
    inspector = inspect(db_session.connection())

    assert inspector.has_table("topics")
    assert set(db_session.scalars(select(TopicModel.id))) == INITIAL_TOPIC_IDS


@pytest.mark.integration
def test_migration_constrains_source_category_to_topic_id(db_session: Session):
    inspector = inspect(db_session.connection())
    foreign_keys = inspector.get_foreign_keys("sources")

    assert any(
        foreign_key["constrained_columns"] == ["category"]
        and foreign_key["referred_table"] == "topics"
        and foreign_key["referred_columns"] == ["id"]
        for foreign_key in foreign_keys
    )


@pytest.mark.integration
def test_source_can_reference_an_existing_topic(db_session: Session):
    db_session.add(
        SourceModel(
            id=uuid4(),
            category="science",
            language="en",
            interval_seconds=300,
            enabled=True,
        )
    )

    db_session.flush()


@pytest.mark.integration
def test_source_cannot_reference_an_unknown_topic(db_session: Session):
    db_session.add(
        SourceModel(
            id=uuid4(),
            category="unknown",
            language="en",
            interval_seconds=300,
            enabled=True,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()
