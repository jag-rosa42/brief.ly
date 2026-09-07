from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.infrastructure.database.models import NormalizedArticleModel


@pytest.fixture
def normalized_article_model(source_model) -> NormalizedArticleModel:
    return NormalizedArticleModel(
        id=uuid4(),
        source_id=source_model.id,
        discovered_article_external_id="article-001",
        url="https://example.com/articles/article-001",
        title="Test article",
        publisher_name="Test publisher_name",
        description="Test description",
        content="Test article content",
        authors=["Test Author"],
        image_url="https://example.com/images/article-001.jpg",
        published_at=datetime.now(UTC),
        category="science",
        language="fr",
    )
