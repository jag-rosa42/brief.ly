from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.domain.entities import NormalizedArticle
from src.infrastructure.database.models import NormalizedArticleModel
from src.infrastructure.database.repositories import (
    SqlAlchemyNormalizedArticleRepository,
)


@pytest.mark.integration
def test_save_maps_summary_metadata(
    db_session: Session,
    source_model,
    normalized_article: NormalizedArticle,
):
    summarized_at = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)
    enriched_article = replace(
        normalized_article,
        summary="Article summary",
        summarized_at=summarized_at,
        summary_llm_model="test-model",
    )
    db_session.add(source_model)
    db_session.flush()

    SqlAlchemyNormalizedArticleRepository(db_session).save(
        source_model.id,
        enriched_article,
    )
    db_session.flush()

    persisted = db_session.get(NormalizedArticleModel, enriched_article.id)
    assert persisted is not None
    assert persisted.summary == "Article summary"
    assert persisted.summarized_at == summarized_at
    assert persisted.summary_llm_model == "test-model"


@pytest.mark.integration
def test_lists_articles_by_topic(
    db_session: Session,
    source_model,
    normalized_article: NormalizedArticle,
):
    db_session.add(source_model)
    db_session.flush()
    repository = SqlAlchemyNormalizedArticleRepository(db_session)
    repository.save(source_model.id, normalized_article)
    db_session.flush()

    articles = repository.list_by_topic_id(normalized_article.category, limit=25)

    assert articles == [normalized_article]


@pytest.mark.integration
def test_lists_only_articles_with_missing_summaries(
    db_session: Session,
    source_model,
    normalized_article: NormalizedArticle,
):
    summarized_article = replace(normalized_article, summary="Already summarized")
    missing_article = replace(
        normalized_article,
        id=uuid4(),
        discovered_article_external_id="missing-summary",
    )
    db_session.add(source_model)
    db_session.flush()
    repository = SqlAlchemyNormalizedArticleRepository(db_session)
    repository.save(source_model.id, summarized_article)
    repository.save(source_model.id, missing_article)
    db_session.flush()

    articles = repository.list_missing_summary(limit=25)

    assert articles == [missing_article]
