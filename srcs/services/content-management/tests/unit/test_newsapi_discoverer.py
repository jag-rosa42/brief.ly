from datetime import UTC, datetime
from unittest.mock import Mock

from src.infrastructure.clients.article_discovery.newsapi_article_discoverer import (
    NewsApiArticleDiscoverer,
)


def test_discover_queries_newsapi_with_the_source_configuration(source):
    client = Mock()
    client.get_top_headlines.return_value = {"articles": []}

    NewsApiArticleDiscoverer(client).discover(source)

    client.get_top_headlines.assert_called_once_with(
        category="science",
        language="fr",
    )


def test_discover_maps_newsapi_metadata_and_external_identity(source):
    client = Mock()
    client.get_top_headlines.return_value = {
        "articles": [
            {
                "source": {"name": "Le journal des sciences"},
                "author": "Ada Lovelace",
                "description": "Le résumé",
                "url": "https://example.test/articles/42",
                "publishedAt": "2026-08-14T07:15:00Z",
            }
        ]
    }

    articles = NewsApiArticleDiscoverer(client).discover(source)

    assert len(articles) == 1
    article = articles[0]
    assert article.external_id == "https://example.test/articles/42"
    assert article.url == "https://example.test/articles/42"
    assert article.publisher_name == "Le journal des sciences"
    assert article.description == "Le résumé"
    assert article.authors == ["Ada Lovelace"]
    assert article.category == source.category
    assert article.language == source.language
    assert article.published_at == datetime(2026, 8, 14, 7, 15, tzinfo=UTC)


def test_discover_ignores_items_without_a_url(source):
    client = Mock()
    client.get_top_headlines.return_value = {
        "articles": [
            {"source": {"name": "Incomplete"}, "description": "Sans URL"},
            {
                "source": {"name": "Complete"},
                "description": "Avec URL",
                "url": "https://example.test/complete",
            },
        ]
    }

    articles = NewsApiArticleDiscoverer(client).discover(source)

    assert [article.url for article in articles] == ["https://example.test/complete"]


def test_discover_keeps_optional_metadata_optional(source):
    client = Mock()
    client.get_top_headlines.return_value = {
        "articles": [
            {
                "source": {"name": "Minimal"},
                "url": "https://example.test/minimal",
                "description": None,
            }
        ]
    }

    article = NewsApiArticleDiscoverer(client).discover(source)[0]

    assert article.description is None
    assert article.authors is None
    assert article.published_at is None
