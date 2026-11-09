import pytest
from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, inspect
from sqlalchemy.orm import Session


@pytest.mark.integration
def test_migration_extracts_article_summaries_to_a_dedicated_table(
    db_session: Session,
):
    inspector = inspect(db_session.connection())
    article_columns = {
        column["name"] for column in inspector.get_columns("normalized_articles")
    }
    assert {"summary", "summarized_at", "summary_llm_model"}.isdisjoint(article_columns)

    columns = {
        column["name"]: column for column in inspector.get_columns("article_summaries")
    }
    assert set(columns) == {
        "article_id",
        "text",
        "summarized_at",
        "llm_model",
        "rejected",
        "quality_comment",
        "generation_duration_ms",
    }
    assert isinstance(columns["text"]["type"], String)
    assert columns["text"]["type"].length == 2000
    assert isinstance(columns["summarized_at"]["type"], DateTime)
    assert columns["summarized_at"]["type"].timezone
    assert isinstance(columns["rejected"]["type"], Boolean)
    assert isinstance(columns["quality_comment"]["type"], Text)
    assert isinstance(columns["generation_duration_ms"]["type"], BigInteger)
    assert columns["text"]["nullable"]
    assert all(
        not column["nullable"] for name, column in columns.items() if name != "text"
    )

    foreign_keys = inspector.get_foreign_keys("article_summaries")
    assert len(foreign_keys) == 1
    assert foreign_keys[0]["referred_table"] == "normalized_articles"
    assert foreign_keys[0]["referred_columns"] == ["id"]
    assert foreign_keys[0]["options"] == {"ondelete": "CASCADE"}


@pytest.mark.integration
def test_migration_extracts_topic_summaries_to_a_dedicated_table(db_session: Session):
    inspector = inspect(db_session.connection())
    topic_columns = {column["name"] for column in inspector.get_columns("topics")}
    assert {"summary", "summarized_at", "summary_llm_model"}.isdisjoint(topic_columns)

    columns = {
        column["name"]: column for column in inspector.get_columns("topic_summaries")
    }
    assert set(columns) == {
        "topic_id",
        "text",
        "summarized_at",
        "llm_model",
        "generation_duration_ms",
    }
    assert isinstance(columns["text"]["type"], String)
    assert columns["text"]["type"].length == 2000
    assert isinstance(columns["summarized_at"]["type"], DateTime)
    assert columns["summarized_at"]["type"].timezone
    assert isinstance(columns["generation_duration_ms"]["type"], BigInteger)
    assert columns["generation_duration_ms"]["nullable"]
    assert all(
        not column["nullable"]
        for name, column in columns.items()
        if name != "generation_duration_ms"
    )
