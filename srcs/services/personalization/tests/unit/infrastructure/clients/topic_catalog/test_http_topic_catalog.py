from collections.abc import Callable

import httpx2 as httpx
import pytest

from src.application.exceptions import TopicCatalogUnavailableError
from src.domain.entities.topic import Topic
from src.infrastructure.clients.topic_catalog.http_topic_catalog import (
    TOPICS_PATH,
    HttpTopicCatalog,
)

BASE_URL = "http://content-management"


def _catalog(handler: Callable[[httpx.Request], httpx.Response]) -> HttpTopicCatalog:
    """Build a catalog whose HTTP calls are answered by `handler` instead of CM."""
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=BASE_URL)
    return HttpTopicCatalog(BASE_URL, client=client)


def test_get_all_returns_topics_indexed_by_id() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": "science"}, {"id": "health"}])

    topics = _catalog(handler).get_all()

    assert topics == {
        "science": Topic(id="science"),
        "health": Topic(id="health"),
    }


def test_get_all_calls_the_topics_endpoint() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=[])

    _catalog(handler).get_all()

    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == TOPICS_PATH


def test_get_all_raises_when_content_management_returns_an_error() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(500, json=[])

    with pytest.raises(TopicCatalogUnavailableError):
        _catalog(handler).get_all()


def test_get_all_raises_when_content_management_times_out() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout")

    with pytest.raises(TopicCatalogUnavailableError) as exc_info:
        _catalog(handler).get_all()

    assert isinstance(exc_info.value.__cause__, httpx.ConnectTimeout)


def test_get_all_raises_when_content_management_is_down() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection error")

    with pytest.raises(TopicCatalogUnavailableError):
        _catalog(handler).get_all()


def test_get_all_raises_when_the_response_has_no_id() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"name": "Science"}])

    with pytest.raises(TopicCatalogUnavailableError):
        _catalog(handler).get_all()
