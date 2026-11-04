from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    String,
    Table,
    Text,
    UniqueConstraint,
    inspect,
)

from src.infrastructure.database.models import ArticleSummaryModel, NormalizedArticleModel


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
    } <= set(table.columns.keys())

    assert isinstance(table.columns["content"].type, Text)
    assert {"summary", "summarized_at", "summary_llm_model"}.isdisjoint(
        table.columns.keys()
    )

    assert {foreign_key.target_fullname for foreign_key in table.foreign_keys} == {
        "sources.id"
    }

    unique_column_sets = {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("source_id", "discovered_article_external_id") in unique_column_sets


def test_article_summary_model_declares_the_required_persistence_contract():
    table = inspect(ArticleSummaryModel).local_table
    assert isinstance(table, Table)

    assert set(table.columns.keys()) == {
        "article_id",
        "text",
        "summarized_at",
        "llm_model",
        "rejected",
        "quality_comment",
        "generation_duration_ms",
    }
    assert table.primary_key.columns.keys() == ["article_id"]
    assert isinstance(table.columns["text"].type, String)
    assert table.columns["text"].type.length == 2000
    assert isinstance(table.columns["summarized_at"].type, DateTime)
    assert table.columns["summarized_at"].type.timezone
    assert isinstance(table.columns["rejected"].type, Boolean)
    assert isinstance(table.columns["quality_comment"].type, Text)
    assert isinstance(table.columns["generation_duration_ms"].type, BigInteger)
    assert all(not column.nullable for column in table.columns)

    foreign_key = next(iter(table.foreign_keys))
    assert foreign_key.target_fullname == "normalized_articles.id"
    assert foreign_key.ondelete == "CASCADE"
    assert any(
        isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_article_summaries_generation_duration_ms_nonnegative"
        for constraint in table.constraints
    )
