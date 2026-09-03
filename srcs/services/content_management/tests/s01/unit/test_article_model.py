from sqlalchemy import UniqueConstraint, inspect

from src.infrastructure.database.models import ArticleModel


def test_article_model_declares_the_required_persistence_contract():
    table = inspect(ArticleModel).local_table

    assert {
        "id",
        "source_id",
        "external_id",
        "title",
        "content",
        "authors",
        "url",
        "image_url",
        "published_at",
        "fetched_at",
    } <= set(table.columns.keys())

    assert {
            foreign_key.target_fullname for foreign_key in table.foreign_keys
            } == {"sources.id"}

    unique_column_sets = {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("source_id", "external_id") in unique_column_sets
