from collections.abc import Callable
from typing import Any
from uuid import UUID

import httpx2 as httpx
import pytest
from shared_auth import DownstreamClient, DownstreamError
from shared_errors import InfrastructureError

from src.application.exceptions import ArticleCatalogUnavailableError
from src.domain.entities.article import Article
from src.infrastructure.clients.article_catalog.http_article_catalog import (
    ARTICLES_PATH,
    HttpArticleCatalog,
)
from src.infrastructure.clients.service_token_provider import ServiceTokenProvider
from tests.fakes import FakeServiceTokenProvider

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


def _catalog(
    handler: Callable[[httpx.Request], httpx.Response],
    token_provider: ServiceTokenProvider | None = None,
) -> HttpArticleCatalog:
    """Build a catalog whose HTTP calls are answered by `handler` instead of CM."""
    client = DownstreamClient(
        "content-management", BASE_URL, transport=httpx.MockTransport(handler)
    )
    return HttpArticleCatalog(client, token_provider or FakeServiceTokenProvider())


def test_find_by_id_returns_the_article() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=ARTICLE_JSON)

    article = _catalog(handler).find_by_id(ARTICLE_ID)

    assert article == Article(
        article_id=ARTICLE_ID,
        title="Open-source models narrow the enterprise gap",
        source="TechDaily",
        topic_id="technology",
        summary="Smaller teams gain access to capable models.",
        url="https://www.aitechdaily.com/",
        read_time_minutes=3,
    )


def test_find_by_id_keeps_a_missing_summary() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=ARTICLE_JSON | {"summary": None})

    article = _catalog(handler).find_by_id(ARTICLE_ID)

    assert article is not None
    assert article.summary is None


def test_find_by_id_calls_the_article_endpoint() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=ARTICLE_JSON)

    _catalog(handler).find_by_id(ARTICLE_ID)

    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == ARTICLES_PATH.format(article_id=ARTICLE_ID)


def test_find_by_id_returns_none_when_the_article_is_unknown() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"code": "ARTICLE_NOT_FOUND"}})

    assert _catalog(handler).find_by_id(ARTICLE_ID) is None


def test_find_by_id_raises_when_content_management_returns_an_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={})

    with pytest.raises(ArticleCatalogUnavailableError):
        _catalog(handler).find_by_id(ARTICLE_ID)


def test_find_by_id_raises_when_content_management_is_down() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection error")

    with pytest.raises(ArticleCatalogUnavailableError) as exc_info:
        _catalog(handler).find_by_id(ARTICLE_ID)

    assert isinstance(exc_info.value.__cause__, InfrastructureError)


def test_find_by_id_raises_when_a_field_is_missing() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        article_json = dict(ARTICLE_JSON)
        del article_json["publisher_name"]
        return httpx.Response(200, json=article_json)

    with pytest.raises(ArticleCatalogUnavailableError):
        _catalog(handler).find_by_id(ARTICLE_ID)


def test_find_by_id_raises_when_the_article_id_is_not_a_uuid() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=ARTICLE_JSON | {"article_id": "not-a-uuid"})

    with pytest.raises(ArticleCatalogUnavailableError):
        _catalog(handler).find_by_id(ARTICLE_ID)


def test_find_by_id_sends_the_service_token() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=ARTICLE_JSON)

    _catalog(handler, FakeServiceTokenProvider(token="abc")).find_by_id(ARTICLE_ID)

    assert requests[0].headers["Authorization"] == "Bearer abc"


@pytest.mark.parametrize(
    "token_error",
    [
        InfrastructureError("Identity is down"),
        DownstreamError(service="identity", status_code=401, code="INVALID_CLIENT"),
    ],
    ids=["identity-unreachable", "identity-refuses"],
)
def test_find_by_id_raises_without_calling_content_management_when_no_token(
    token_error: Exception,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=ARTICLE_JSON)

    with pytest.raises(ArticleCatalogUnavailableError):
        _catalog(handler, FakeServiceTokenProvider(error=token_error)).find_by_id(
            ARTICLE_ID
        )

    assert requests == []


def test_find_by_id_raises_when_our_service_token_expired() -> None:
    """Content Management's 401 TOKEN_EXPIRED is about our service token: it
    becomes "unavailable", never the user's TOKEN_EXPIRED."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"code": "TOKEN_EXPIRED"}})

    with pytest.raises(ArticleCatalogUnavailableError):
        _catalog(handler).find_by_id(ARTICLE_ID)
