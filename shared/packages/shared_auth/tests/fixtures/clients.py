"""
Fakes for the HTTP clients: no network, no sleeping.

- httpx2.MockTransport answers requests with a Python function instead of the
  network: it plays the downstream service, or the token endpoint.
- FakeClock replaces time.monotonic, so a test can "wait" 5 minutes instantly.
"""

import time
from collections.abc import Callable

import httpx2
import pytest
from pydantic import SecretStr

from shared_auth.infrastructure.clients.client_credentials_token_provider import (
    ClientCredentialsTokenProvider,
)
from shared_auth.infrastructure.clients.downstream_client import DownstreamClient
from tests.fixtures.factory import (
    OTHER_SERVICE_AUDIENCE,
    READ_SCOPE,
    SERVICE_NAME,
    WRITE_SCOPE,
)

Handler = Callable[[httpx2.Request], httpx2.Response]

ISSUER_SERVICE: str = "issuer-service"
# Made-up hosts: MockTransport never resolves them.
TOKEN_ENDPOINT_URL: str = "http://issuer.test/oauth/token"
CLIENT_ID: str = SERVICE_NAME
CLIENT_SECRET: str = "s3cret"
# The service tokens are requested for another service.
TARGET_AUDIENCE: str = OTHER_SERVICE_AUDIENCE
TARGET_SCOPES: tuple[str, ...] = (WRITE_SCOPE, READ_SCOPE)
DOWNSTREAM_SERVICE: str = "downstream-service"
DOWNSTREAM_BASE_URL: str = "http://downstream.test"


# ---------------------------------------------------------------------------
# Fake clock
# ---------------------------------------------------------------------------


class FakeClock:
    """Stands in for time.monotonic: time only moves when the test says so."""

    def __init__(self) -> None:
        self.now: float = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


# ---------------------------------------------------------------------------
# Fake token endpoint
# ---------------------------------------------------------------------------


class FakeTokenEndpoint:
    """Answers client credentials requests, and records them.

    Each new token is numbered ("service-token-1", "service-token-2", ...),
    so a test can tell a cached token from a renewed one.
    """

    def __init__(self, expires_in: int = 300) -> None:
        self.requests: list[httpx2.Request] = []
        self.expires_in: int = expires_in
        # Seconds to wait before answering: lets concurrent callers pile up.
        self.delay: float = 0.0

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        if self.delay:
            time.sleep(self.delay)
        return httpx2.Response(
            200,
            json={
                "access_token": f"service-token-{len(self.requests)}",
                "token_type": "Bearer",
                "expires_in": self.expires_in,
            },
        )


@pytest.fixture
def token_endpoint() -> FakeTokenEndpoint:
    return FakeTokenEndpoint()


# ---------------------------------------------------------------------------
# Clients under test
# ---------------------------------------------------------------------------


@pytest.fixture
def make_token_provider(
    clock: FakeClock,
) -> Callable[[Handler], ClientCredentialsTokenProvider]:
    """Build a token provider whose token endpoint is `handler`."""

    def _make(handler: Handler) -> ClientCredentialsTokenProvider:
        return ClientCredentialsTokenProvider(
            issuer_service=ISSUER_SERVICE,
            token_endpoint_url=TOKEN_ENDPOINT_URL,
            client_id=CLIENT_ID,
            client_secret=SecretStr(CLIENT_SECRET),
            audience=TARGET_AUDIENCE,
            scopes=TARGET_SCOPES,
            transport=httpx2.MockTransport(handler),
            clock=clock,
        )

    return _make


@pytest.fixture
def make_downstream_client() -> Callable[[Handler], DownstreamClient]:
    """Build a DownstreamClient whose downstream service is `handler`."""

    def _make(handler: Handler) -> DownstreamClient:
        return DownstreamClient(
            DOWNSTREAM_SERVICE,
            DOWNSTREAM_BASE_URL,
            transport=httpx2.MockTransport(handler),
        )

    return _make
