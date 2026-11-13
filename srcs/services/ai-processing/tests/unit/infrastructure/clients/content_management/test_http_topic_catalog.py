from collections.abc import Callable

import httpx2 as httpx
import pytest
from shared_auth import DownstreamClient, DownstreamError

from src.application.exceptions import TopicCatalogUnavailableError
from src.infrastructure.clients.content_management.http_topic_catalog import (
    TOPICS_PATH,
    HttpTopicCatalog,
)
from tests.fakes import FakeServiceTokenProvider

BASE_URL = "http://content-management"


def _catalog(
    handler: Callable[[httpx.Request], httpx.Response],
    token_provider: FakeServiceTokenProvider | None = None,
) -> HttpTopicCatalog:
    client = DownstreamClient(
        "content-management", BASE_URL, transport=httpx.MockTransport(handler)
    )
    return HttpTopicCatalog(client, token_provider or FakeServiceTokenProvider())


def test_get_summaries_indexes_the_summaries_by_topic() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json=[
                {"id": "business", "summary": "Markets rose."},
                {"id": "health", "summary": None},
            ],
        )

    assert _catalog(handler).get_summaries() == {
        "business": "Markets rose.",
        "health": None,
    }
    assert seen[0].url.path == TOPICS_PATH
    assert seen[0].headers["Authorization"] == "Bearer service-token"


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(503),
        httpx.Response(401, json={"error": {"code": "TOKEN_EXPIRED", "message": "x"}}),
        httpx.Response(200, content=b"not json"),
        httpx.Response(200, json=[{"summary": "no id"}]),
        httpx.Response(200, json=["not an object"]),
        httpx.Response(200, json=[{"id": "business", "summary": 3}]),
    ],
)
def test_get_summaries_turns_every_failure_into_unavailable(
    response: httpx.Response,
) -> None:
    with pytest.raises(TopicCatalogUnavailableError):
        _catalog(lambda _request: response).get_summaries()


def test_get_summaries_is_unavailable_when_identity_refuses_the_token() -> None:
    provider = FakeServiceTokenProvider(
        error=DownstreamError("identity", 401, "INVALID_CLIENT")
    )

    with pytest.raises(TopicCatalogUnavailableError):
        _catalog(lambda _request: httpx.Response(200, json=[]), provider).get_summaries()
