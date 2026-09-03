from datetime import UTC, datetime
from unittest.mock import Mock, patch
from uuid import uuid4

from src.domain.entities.discovered_article import DiscoveredArticle
from src.domain.entities.extracted_article import ExtractedArticle
from src.infrastructure.article_extraction.newspaper_extractor import (
    NewspaperExtractor,
)


def _discovered(**overrides):
    values = {
        "external_id": "article-42",
        "url": "https://example.test/articles/42",
        "editor": "Example",
        "description": "Résumé",
        "authors": ["Auteur NewsAPI"],
        "published_at": datetime(2026, 8, 14, 7, 15, tzinfo=UTC),
        "category": "science",
        "language": "fr",
    }
    values.update(overrides)
    return DiscoveredArticle(**values)


@patch("src.infrastructure.article_extraction.newspaper_extractor.Article")
def test_extract_downloads_and_parses_the_discovered_url(article_factory):
    downloaded = Mock()
    downloaded.id = uuid4()
    downloaded.title = "Titre extrait"
    downloaded.text = "Contenu extrait"
    downloaded.authors = ["Ada Lovelace"]
    downloaded.top_image = "https://example.test/extracted.jpg"
    downloaded.publish_date = datetime(2026, 8, 14, 8, tzinfo=UTC)
    article_factory.return_value = downloaded

    result = NewspaperExtractor().extract(_discovered())

    article_factory.assert_called_once_with("https://example.test/articles/42")
    downloaded.download.assert_called_once_with()
    downloaded.parse.assert_called_once_with()
    assert isinstance(result, ExtractedArticle)


@patch("src.infrastructure.article_extraction.newspaper_extractor.Article")
def test_extract_builds_the_complete_persistable_article(article_factory):
    downloaded = Mock(
        id=uuid4(),
        title="Titre extrait",
        text="Contenu extrait",
        authors=["Ada Lovelace", "Grace Hopper"],
        top_image="https://example.test/extracted.jpg",
        url="https://example.test/articles/42",
    )
    article_factory.return_value = downloaded
    discovered = _discovered()
    expected_id = uuid4()
    uuid_factory = Mock(return_value=expected_id)

    result = NewspaperExtractor(uuid_factory=uuid_factory).extract(discovered)

    uuid_factory.assert_called_once_with()
    assert result == ExtractedArticle(
        id=expected_id,
        external_id="article-42",
        url="https://example.test/articles/42",
        editor="Example",
        title="Titre extrait",
        description="Résumé",
        content="Contenu extrait",
        authors=["Ada Lovelace", "Grace Hopper"],
        image_url="https://example.test/extracted.jpg",
        category="science",
        language="fr",
        published_at=datetime(2026, 8, 14, 7, 15, tzinfo=UTC),
    )


@patch("src.infrastructure.article_extraction.newspaper_extractor.Article")
def test_extract_retains_the_discovered_external_identity(article_factory):
    downloaded = Mock(
        title="Titre extrait",
        text="Contenu extrait",
        authors=[],
        top_image="",
        url="https://example.test/articles/canonical-url",
    )
    article_factory.return_value = downloaded
    discovered = _discovered(external_id="newsapi-identity")

    result = NewspaperExtractor().extract(discovered)

    assert result.external_id == "newsapi-identity"
