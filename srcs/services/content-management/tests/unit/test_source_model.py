from sqlalchemy import inspect

from src.infrastructure.database.models import SourceModel


def test_source_category_references_a_topic():
    table = inspect(SourceModel).local_table

    assert {foreign_key.target_fullname for foreign_key in table.foreign_keys} == {
        "topics.id"
    }
