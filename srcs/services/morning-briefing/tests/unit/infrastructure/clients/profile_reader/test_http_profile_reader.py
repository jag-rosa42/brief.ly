from collections.abc import Callable
from uuid import UUID

import httpx2 as httpx
import pytest
from shared_auth import DownstreamClient, DownstreamError, TokenExpiredError
from shared_errors.exceptions import InfrastructureError

from src.application.exceptions import ProfileReaderUnavailableError
from src.domain.entities.profile import Profile
from src.infrastructure.clients.profile_reader.http_profile_reader import (
    PROFILE_PATH,
    HttpProfileReader,
)

BASE_URL = "http://personalization"
TOKEN = "user-token"
SAVED_ARTICLE_ID = UUID("6f1c1b2e-1d2a-4c3b-9a8e-111111111111")
PROFILE_JSON = {
    "account_id": "1b71e72d-9194-4438-af41-cc39af09de31",
    "name": "John",
    "topic_ids": ["business", "science"],
    "saved_article_ids": [str(SAVED_ARTICLE_ID)],
}


def _reader(handler: Callable[[httpx.Request], httpx.Response]) -> HttpProfileReader:
    """Build a reader answered by `handler` instead of Personalization."""
    client = DownstreamClient(
        "personalization", BASE_URL, transport=httpx.MockTransport(handler)
    )
    return HttpProfileReader(client)


def _error(status: int, code: str) -> httpx.Response:
    return httpx.Response(status, json={"error": {"code": code, "message": code}})


def test_get_returns_the_profile() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=PROFILE_JSON)

    assert _reader(handler).get(TOKEN) == Profile(
        name="John",
        topic_ids=("business", "science"),
        saved_article_ids=(SAVED_ARTICLE_ID,),
    )


def test_get_forwards_the_user_token() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=PROFILE_JSON)

    _reader(handler).get(TOKEN)

    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == PROFILE_PATH
    assert requests[0].headers["Authorization"] == f"Bearer {TOKEN}"


def test_get_returns_none_without_a_profile() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _error(404, "PROFILE_NOT_FOUND")

    assert _reader(handler).get(TOKEN) is None


def test_get_passes_an_expired_token_through() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _error(401, "TOKEN_EXPIRED")

    with pytest.raises(TokenExpiredError):
        _reader(handler).get(TOKEN)


def test_get_raises_when_personalization_is_down() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection error")

    with pytest.raises(InfrastructureError):
        _reader(handler).get(TOKEN)


def test_get_raises_on_another_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return _error(404, "SOMETHING_ELSE")

    with pytest.raises(DownstreamError):
        _reader(handler).get(TOKEN)


def test_get_raises_when_the_response_is_invalid() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=PROFILE_JSON | {"saved_article_ids": ["nope"]})

    with pytest.raises(ProfileReaderUnavailableError):
        _reader(handler).get(TOKEN)


def test_get_raises_when_the_response_is_not_json() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json")

    with pytest.raises(ProfileReaderUnavailableError):
        _reader(handler).get(TOKEN)
