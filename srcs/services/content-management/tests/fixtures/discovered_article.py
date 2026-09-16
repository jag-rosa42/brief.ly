import pytest

from src.domain.entities import DiscoveredArticle


@pytest.fixture
def discovered_article(synchronization_time) -> DiscoveredArticle:
    return DiscoveredArticle(
        external_id="science-fr",
        url="https://example.com/fakeurl",
        publisher_name="Fred",
        description="nothing much",
        authors=["Roberto"],
        published_at=synchronization_time,
        category="science",
        language="fr",
    )
