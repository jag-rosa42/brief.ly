from sqlalchemy import BigInteger, String, Table, inspect

from src.infrastructure.database.models import TopicModel, TopicSummaryModel


def test_topic_model_declares_the_required_persistence_contract():
    table = inspect(TopicModel).local_table

    assert isinstance(table, Table)
    assert table.name == "topics"
    assert tuple(table.columns.keys()) == ("id",)
    assert isinstance(table.columns["id"].type, String)
    assert tuple(table.primary_key.columns.keys()) == ("id",)


def test_topic_summary_model_declares_the_common_persistence_contract():
    table = inspect(TopicSummaryModel).local_table

    assert isinstance(table, Table)
    assert tuple(table.columns.keys()) == (
        "topic_id",
        "text",
        "summarized_at",
        "llm_model",
        "generation_duration_ms",
    )
    assert tuple(table.primary_key.columns.keys()) == ("topic_id",)
    assert isinstance(table.columns["text"].type, String)
    assert table.columns["text"].type.length == 2000
    assert isinstance(table.columns["generation_duration_ms"].type, BigInteger)
    assert table.columns["generation_duration_ms"].nullable
    assert all(
        not column.nullable
        for column in table.columns
        if column.name != "generation_duration_ms"
    )
    foreign_key = next(iter(table.foreign_keys))
    assert foreign_key.target_fullname == "topics.id"
    assert foreign_key.ondelete == "CASCADE"
