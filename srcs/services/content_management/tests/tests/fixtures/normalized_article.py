from uuid import uuid4

import pytest

from src.domain.entities import NormalizedArticle


@pytest.fixture
def normalized_article(synchronization_time) -> NormalizedArticle:
    return NormalizedArticle(
        id=uuid4(),
        discovered_article_external_id="science-fr",
        url="https://example.com/fakeurl",
        publisher_name="Jerem",
        title="fakeArticle",
        description="nothing much",
        content="No content for now",
        authors=["Roberto"],
        image_url="fake_image_url.com",
        published_at=synchronization_time,
        category="science",
        language="fr",
    )
