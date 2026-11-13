from collections.abc import Callable

import httpx2 as httpx
import pytest
from shared_auth import DownstreamClient, DownstreamError, TokenExpiredError
from shared_errors.exceptions import InfrastructureError

from src.application.exceptions import ProfileReaderUnavailableError
from src.infrastructure.clients.personalization.http_profile_reader import (
    PROFILE_PATH,
    HttpProfileReader,
)

BASE_URL = "http://personalization"
TOKEN = "user-token"
PROFILE_JSON = {
    "account_id": "1b71e72d-9194-4438-af41-cc39af09de31",
    "name": "John",
    "topic_ids": ["business", "science"],
    "saved_article_ids": [],
}


def _reader(handler: Callable[[httpx.Request], httpx.Response]) -> HttpProfileReader:
    """Build a reader answered by `handler` instead of Personalization."""
    client = DownstreamClient(
        "personalization", BASE_URL, transport=httpx.MockTransport(handler)
    )
    return HttpProfileReader(client)


def _error(status: int, code: str) -> httpx.Response:
    return httpx.Response(status, json={"error": {"code": code, "message": code}})


def test_get_topic_ids_returns_the_topics_in_order() -> None:
    reader = _reader(lambda _request: httpx.Response(200, json=PROFILE_JSON))

    assert reader.get_topic_ids(TOKEN) == ("business", "science")


def test_get_topic_ids_forwards_the_user_token() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=PROFILE_JSON)

    _reader(handler).get_topic_ids(TOKEN)

    assert seen[0].url.path == PROFILE_PATH
    assert seen[0].headers["Authorization"] == f"Bearer {TOKEN}"


def test_get_topic_ids_is_empty_without_a_profile() -> None:
    reader = _reader(lambda _request: _error(404, "PROFILE_NOT_FOUND"))

    assert reader.get_topic_ids(TOKEN) == ()


def test_get_topic_ids_passes_on_an_expired_token() -> None:
    reader = _reader(lambda _request: _error(401, "TOKEN_EXPIRED"))

    with pytest.raises(TokenExpiredError):
        reader.get_topic_ids(TOKEN)


def test_get_topic_ids_passes_on_other_errors() -> None:
    reader = _reader(lambda _request: _error(404, "NOT_FOUND"))

    with pytest.raises(DownstreamError):
        reader.get_topic_ids(TOKEN)


def test_get_topic_ids_raises_infrastructure_error_when_unavailable() -> None:
    reader = _reader(lambda _request: _error(503, "SERVICE_UNAVAILABLE"))

    with pytest.raises(InfrastructureError):
        reader.get_topic_ids(TOKEN)


@pytest.mark.parametrize(
    "body",
    [b"not json", b"{}", b'{"topic_ids": "business"}', b'{"topic_ids": [1]}'],
)
def test_get_topic_ids_rejects_an_unexpected_body(body: bytes) -> None:
    reader = _reader(lambda _request: httpx.Response(200, content=body))

    with pytest.raises(ProfileReaderUnavailableError):
        reader.get_topic_ids(TOKEN)
