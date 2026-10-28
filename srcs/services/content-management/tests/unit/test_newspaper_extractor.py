from datetime import UTC, datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from newspaper import ArticleException

from src.application.port import ArticleExtractionError
from src.domain.entities import DiscoveredArticle, NormalizedArticle
from src.infrastructure.clients.article_extraction.newspaper_article_extractor import (
    NewspaperArticleExtractor,
)


def _discovered_article(**overrides):
    values = {
        "external_id": "article-42",
        "url": "https://example.test/articles/42",
        "publisher_name": "Example",
        "description": "Résumé",
        "authors": ["Auteur NewsAPI"],
        "published_at": datetime(2026, 8, 14, 7, 15, tzinfo=UTC),
        "category": "science",
        "language": "fr",
    }
    values.update(overrides)
    return DiscoveredArticle(**values)


@patch(
    "src.infrastructure.clients.article_extraction.newspaper_article_extractor.NewspaperArticle"
)
def test_extract_downloads_and_parses_the_discovered_article_url(
    discovered_article_factory,
):
    downloaded = Mock()
    downloaded.id = uuid4()
    downloaded.title = "Titre extrait"
    downloaded.text = "Contenu extrait"
    downloaded.authors = ["Ada Lovelace"]
    downloaded.top_image = "https://example.test/normalized_article.jpg"
    downloaded.publish_date = datetime(2026, 8, 14, 8, tzinfo=UTC)
    discovered_article_factory.return_value = downloaded

    result = NewspaperArticleExtractor().extract(_discovered_article())

    discovered_article_factory.assert_called_once_with("https://example.test/articles/42")
    downloaded.download.assert_called_once_with()
    downloaded.parse.assert_called_once_with()
    assert isinstance(result, NormalizedArticle)


@patch(
    "src.infrastructure.clients.article_extraction.newspaper_article_extractor.NewspaperArticle"
)
def test_extract_builds_the_complete_persistable_article(discovered_article_factory):
    downloaded = Mock(
        id=uuid4(),
        title="Titre extrait",
        text="Contenu extrait",
        authors=["Ada Lovelace", "Grace Hopper"],
        top_image="https://example.test/normalized_article.jpg",
        url="https://example.test/articles/42",
    )
    discovered_article_factory.return_value = downloaded
    discovered_article = _discovered_article()
    expected_id = uuid4()
    uuid_factory = Mock(return_value=expected_id)

    result = NewspaperArticleExtractor(uuid_factory=uuid_factory).extract(
        discovered_article
    )

    uuid_factory.assert_called_once_with()
    assert result == NormalizedArticle(
        id=expected_id,
        discovered_article_external_id="article-42",
        url="https://example.test/articles/42",
        publisher_name="Example",
        title="Titre extrait",
        description="Résumé",
        content="Contenu extrait",
        authors=["Ada Lovelace", "Grace Hopper"],
        image_url="https://example.test/normalized_article.jpg",
        category="science",
        language="fr",
        published_at=datetime(2026, 8, 14, 7, 15, tzinfo=UTC),
    )


@patch(
    "src.infrastructure.clients.article_extraction.newspaper_article_extractor.NewspaperArticle"
)
def test_extract_retains_the_discovered_article_external_identity(
    discovered_article_factory,
):
    downloaded = Mock(
        title="Titre extrait",
        text="Contenu extrait",
        authors=[],
        top_image="",
        url="https://example.test/articles/canonical-url",
    )
    discovered_article_factory.return_value = downloaded
    discovered_article = _discovered_article(external_id="newsapi-identity")

    result = NewspaperArticleExtractor().extract(discovered_article)

    assert result.discovered_article_external_id == "newsapi-identity"


@patch(
    "src.infrastructure.clients.article_extraction.newspaper_article_extractor.NewspaperArticle"
)
def test_translates_newspaper_failures(discovered_article_factory):
    downloaded = Mock()
    downloaded.download.side_effect = ArticleException("download failed")
    discovered_article_factory.return_value = downloaded

    with pytest.raises(ArticleExtractionError, match="Unable to extract article"):
        NewspaperArticleExtractor().extract(_discovered_article())
