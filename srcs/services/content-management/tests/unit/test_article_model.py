from sqlalchemy import DateTime, String, Table, Text, UniqueConstraint, inspect

from src.infrastructure.database.models import NormalizedArticleModel


def test_normalized_article_model_declares_the_required_persistence_contract():
    table = inspect(NormalizedArticleModel).local_table
    assert isinstance(table, Table)

    assert {
        "id",
        "source_id",
        "discovered_article_external_id",
        "title",
        "content",
        "authors",
        "url",
        "image_url",
        "published_at",
        "fetched_at",
        "summary",
        "summarized_at",
        "summary_llm_model",
    } <= set(table.columns.keys())

    assert isinstance(table.columns["content"].type, Text)
    assert isinstance(table.columns["summary"].type, String)
    assert table.columns["summary"].type.length == 2000
    assert table.columns["summary"].nullable
    assert isinstance(table.columns["summarized_at"].type, DateTime)
    assert table.columns["summarized_at"].type.timezone
    assert table.columns["summarized_at"].nullable
    assert isinstance(table.columns["summary_llm_model"].type, String)
    assert table.columns["summary_llm_model"].nullable

    assert {foreign_key.target_fullname for foreign_key in table.foreign_keys} == {
        "sources.id"
    }

    unique_column_sets = {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("source_id", "discovered_article_external_id") in unique_column_sets
