from collections.abc import Callable
from typing import Any
from uuid import UUID

import httpx2 as httpx
import pytest

from src.application.exceptions import ArticleCatalogUnavailableError
from src.domain.entities.article import Article
from src.infrastructure.clients.article_catalog.http_article_catalog import (
    ARTICLES_PATH,
    HttpArticleCatalog,
)

BASE_URL = "http://content-management"
ARTICLE_ID = UUID("6f1c1b2e-1d2a-4c3b-9a8e-111111111111")

# The article object of Content Management, with the fields we don't keep.
ARTICLE_JSON: dict[str, Any] = {
    "article_id": str(ARTICLE_ID),
    "title": "Open-source models narrow the enterprise gap",
    "publisher_name": "TechDaily",
    "url": "https://www.aitechdaily.com/",
    "topic_id": "technology",
    "read_time_minutes": 3,
    "summary": "Smaller teams gain access to capable models.",
    "summarized_at": "2026-11-03T08:00:00Z",
    "rejected": False,
    "quality_comment": None,
    "generation_duration_ms": 1200,
}


def _catalog(handler: Callable[[httpx.Request], httpx.Response]) -> HttpArticleCatalog:
    """Build a catalog whose HTTP calls are answered by `handler` instead of CM."""
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=BASE_URL)
    return HttpArticleCatalog(BASE_URL, client=client)


def test_list_by_topic_returns_the_articles() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"items": [ARTICLE_JSON]})

    assert _catalog(handler).list_by_topic("technology") == [
        Article(
            article_id=ARTICLE_ID,
            title="Open-source models narrow the enterprise gap",
            publisher_name="TechDaily",
            url="https://www.aitechdaily.com/",
            summary="Smaller teams gain access to capable models.",
            read_time_minutes=3,
            topic_id="technology",
        )
    ]


def test_list_by_topic_calls_the_articles_endpoint_with_the_topic() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"items": []})

    _catalog(handler).list_by_topic("technology")

    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == ARTICLES_PATH
    assert requests[0].url.params["topic_id"] == "technology"


def test_list_by_topic_returns_an_empty_list_for_an_unknown_topic() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"code": "TOPIC_NOT_FOUND"}})

    assert _catalog(handler).list_by_topic("pseudoscience") == []


def test_list_by_topic_raises_when_content_management_returns_an_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    with pytest.raises(ArticleCatalogUnavailableError):
        _catalog(handler).list_by_topic("technology")


def test_list_by_topic_raises_when_content_management_is_down() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection error")

    with pytest.raises(ArticleCatalogUnavailableError):
        _catalog(handler).list_by_topic("technology")


def test_list_by_topic_raises_when_a_field_is_missing() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        article_json = dict(ARTICLE_JSON)
        del article_json["publisher_name"]
        return httpx.Response(200, json={"items": [article_json]})

    with pytest.raises(ArticleCatalogUnavailableError):
        _catalog(handler).list_by_topic("technology")
