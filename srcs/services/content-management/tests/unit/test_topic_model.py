from sqlalchemy import String, Table, inspect

from src.infrastructure.database.models import TopicModel


def test_topic_model_declares_the_required_persistence_contract():
    table = inspect(TopicModel).local_table

    assert isinstance(table, Table)
    assert table.name == "topics"
    assert tuple(table.columns.keys()) == ("id",)
    assert isinstance(table.columns["id"].type, String)
    assert tuple(table.primary_key.columns.keys()) == ("id",)
