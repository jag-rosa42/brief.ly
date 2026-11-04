from dataclasses import replace

import pytest
from sqlalchemy.orm import Session

from src.domain.entities import ArticleSummary, NormalizedArticle
from src.infrastructure.database.models import NormalizedArticleModel
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
