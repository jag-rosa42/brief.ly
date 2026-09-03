from datetime import UTC, datetime
import pytest

from src.domain.entities.discovered_article import DiscoveredArticle
from src.domain.entities.extracted_article import ExtractedArticle
from src.domain.entities.source import Source


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
