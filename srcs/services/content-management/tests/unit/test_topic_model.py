from sqlalchemy import DateTime, String, Table, inspect

from src.infrastructure.database.models import TopicModel


def test_topic_model_declares_the_required_persistence_contract():
    table = inspect(TopicModel).local_table

    assert isinstance(table, Table)
    assert table.name == "topics"
    assert tuple(table.columns.keys()) == (
        "id",
        "summary",
        "summarized_at",
        "summary_llm_model",
    )
    assert isinstance(table.columns["id"].type, String)
    assert tuple(table.primary_key.columns.keys()) == ("id",)
    assert isinstance(table.columns["summary"].type, String)
    assert table.columns["summary"].type.length == 2000
    assert table.columns["summary"].nullable
    assert isinstance(table.columns["summarized_at"].type, DateTime)
    assert table.columns["summarized_at"].type.timezone
    assert table.columns["summarized_at"].nullable
    assert isinstance(table.columns["summary_llm_model"].type, String)
    assert table.columns["summary_llm_model"].nullable
