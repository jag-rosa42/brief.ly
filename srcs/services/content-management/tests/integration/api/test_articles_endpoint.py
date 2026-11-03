from dataclasses import replace
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.domain.entities import NormalizedArticle
from src.infrastructure.database.repositories import (
    SqlAlchemyNormalizedArticleRepository,
)
from tests import routes


@pytest.mark.integration
def test_get_article_returns_a_persisted_article(
    client: TestClient,
    db_session: Session,
    source_model,
    normalized_article: NormalizedArticle,
) -> None:
    summarized_at = datetime(2026, 11, 3, 12, tzinfo=UTC)
    article = replace(
        normalized_article,
        summary="Article summary",
        summarized_at=summarized_at,
        summary_llm_model="private-model-name",
    )
    db_session.add(source_model)
    db_session.flush()
    SqlAlchemyNormalizedArticleRepository(db_session).save(source_model.id, article)
    db_session.flush()

    response = client.get(routes.ARTICLE_DETAIL.format(article_id=article.id))

    assert response.status_code == 200
    assert response.json() == {
        "article_id": str(article.id),
        "title": article.title,
        "source": article.publisher_name,
        "url": article.url,
        "topic_id": article.category,
        "read_time_minutes": 1,
        "summary": "Article summary",
        "summarized_at": summarized_at.isoformat().replace("+00:00", "Z"),
    }
