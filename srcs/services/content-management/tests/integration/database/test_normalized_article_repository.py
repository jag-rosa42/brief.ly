from dataclasses import replace
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.domain.entities import ArticleSummary, NormalizedArticle
from src.infrastructure.database.models import ArticleSummaryModel, NormalizedArticleModel
from src.infrastructure.database.repositories import (
    SqlAlchemyNormalizedArticleRepository,
)


@pytest.mark.integration
def test_save_maps_summary_metadata(
    db_session: Session,
    source_model,
    normalized_article: NormalizedArticle,
    article_summary: ArticleSummary,
):
    enriched_article = replace(normalized_article, summary=article_summary)
    db_session.add(source_model)
    db_session.flush()

    SqlAlchemyNormalizedArticleRepository(db_session).save(
        source_model.id,
        enriched_article,
    )
    db_session.flush()

    persisted = db_session.get(NormalizedArticleModel, enriched_article.id)
    assert persisted is not None
    assert persisted.summary is not None
    assert persisted.summary.text == article_summary.text
    assert persisted.summary.summarized_at == article_summary.summarized_at
    assert persisted.summary.llm_model == article_summary.llm_model
    assert persisted.summary.rejected is article_summary.rejected
    assert persisted.summary.quality_comment == article_summary.quality_comment
    assert (
        persisted.summary.generation_duration_ms == article_summary.generation_duration_ms
    )


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
    article_summary: ArticleSummary,
):
    summarized_article = replace(normalized_article, summary=article_summary)
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


@pytest.mark.integration
def test_get_by_id_returns_the_persisted_article(
    db_session: Session,
    source_model,
    normalized_article: NormalizedArticle,
):
    db_session.add(source_model)
    db_session.flush()
    repository = SqlAlchemyNormalizedArticleRepository(db_session)
    repository.save(source_model.id, normalized_article)
    db_session.flush()

    result = repository.get_by_id(normalized_article.id)

    assert result == normalized_article


@pytest.mark.integration
def test_get_by_id_returns_none_for_an_unknown_article(db_session: Session):
    assert SqlAlchemyNormalizedArticleRepository(db_session).get_by_id(uuid4()) is None


@pytest.mark.integration
def test_update_summary_persists_metadata(
    db_session: Session,
    source_model,
    normalized_article: NormalizedArticle,
    article_summary: ArticleSummary,
):
    db_session.add(source_model)
    db_session.flush()
    repository = SqlAlchemyNormalizedArticleRepository(db_session)
    repository.save(source_model.id, normalized_article)
    db_session.flush()

    article = repository.update_summary(
        normalized_article.id,
        article_summary,
    )
    db_session.flush()

    persisted = db_session.get(NormalizedArticleModel, normalized_article.id)
    assert article is not None
    assert article.summary == article_summary
    assert persisted is not None
    persisted_summary = db_session.get(ArticleSummaryModel, normalized_article.id)
    assert persisted_summary is not None
    assert persisted_summary.text == article_summary.text
    assert persisted_summary.llm_model == article_summary.llm_model
    assert persisted_summary.summarized_at == article_summary.summarized_at
