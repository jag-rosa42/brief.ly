from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.domain.entities.discovered_article import DiscoveredArticle
from src.domain.entities.extracted_article import ExtractedArticle
from src.domain.entities.source import Source
from src.infrastructure.database.models.article import ArticleModel
from src.infrastructure.database.models.source import SourceModel


@pytest.fixture
def source() -> Source:
    return Source(
        id="science-fr",
        category="science",
        language="fr",
        interval_seconds=300,
        enabled=True,
    )


@pytest.fixture
def source_b() -> Source:
    return Source(
        id="science-en",
        category="science",
        language="en",
        interval_seconds=300,
        enabled=True,
    )


@pytest.fixture
def source_model() -> SourceModel:
    return SourceModel(
        id=uuid4(),
        category="science",
        language="fr",
        interval_seconds=300,
        enabled=True,
    )


@pytest.fixture
def synchronization_time() -> datetime:
    return datetime(2026, 8, 14, 8, 30, tzinfo=UTC)


@pytest.fixture
def discovered(synchronization_time) -> DiscoveredArticle:
    return DiscoveredArticle(
        external_id="science-fr",
        url="https://example.com/fakeurl",
        editor="Fred",
        description="nothing much",
        authors=["Roberto"],
        published_at=synchronization_time,
        category="science",
        language="fr",
    )


@pytest.fixture
def extracted(synchronization_time) -> ExtractedArticle:
    return ExtractedArticle(
        id=uuid4(),
        external_id="science-fr",
        url="https://example.com/fakeurl",
        editor="Jerem",
        title="fakeArticle",
        description="nothing much",
        content="No content for now",
        authors=["Roberto"],
        image_url="fake_image_url.com",
        published_at=synchronization_time,
        category="science",
        language="fr",
    )


@pytest.fixture
def article(source_model) -> ArticleModel:
    return ArticleModel(
        id=uuid4(),
        source_id=source_model.id,
        external_id="article-001",
        url="https://example.com/articles/article-001",
        title="Test article",
        editor="Test editor",
        description="Test description",
        content="Test article content",
        authors=["Test Author"],
        image_url="https://example.com/images/article-001.jpg",
        published_at=datetime.now(UTC),
        category="science",
        language="fr",
    )
