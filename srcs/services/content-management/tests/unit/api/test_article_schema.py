from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.api.schemas import ArticleResponse
from src.domain.entities import ArticleSummary, NormalizedArticle


@pytest.fixture
def normalized_article() -> NormalizedArticle:
    return NormalizedArticle(
        id=uuid4(),
        discovered_article_external_id="science-en",
        url="https://example.com/article",
        publisher_name="Example source",
        title="Example article",
        description=None,
        content="Example article content",
        authors=None,
        image_url=None,
        published_at=None,
        category="science",
        language="en",
    )


def test_maps_an_article_to_the_public_contract(
    normalized_article: NormalizedArticle,
) -> None:
    summarized_at = datetime(2026, 11, 3, 10, tzinfo=UTC)
    article = replace(
        normalized_article,
        summary=ArticleSummary(
            text="A summary",
            summarized_at=summarized_at,
            llm_model="private-model",
            rejected=False,
            quality_comment="Accurate summary",
            generation_duration_ms=750,
        ),
    )

    response = ArticleResponse.from_domain(article)

    assert response.model_dump() == {
        "article_id": article.id,
        "title": article.title,
        "publisher_name": article.publisher_name,
        "url": article.url,
        "topic_id": article.category,
        "content": article.content,
        "read_time_minutes": 1,
        "summary": "A summary",
        "summarized_at": summarized_at,
        "rejected": False,
        "quality_comment": "Accurate summary",
        "generation_duration_ms": 750,
    }
    assert "summary_llm_model" not in type(response).model_fields
