"""
ClientCredentialsTokenProvider: request format, caching, renewal, errors.

The token endpoint is a FakeTokenEndpoint behind an httpx2.MockTransport, and time is a
FakeClock: a test "waits" by calling clock.advance(), never by sleeping.
"""

import base64
import threading
from collections.abc import Callable
from urllib.parse import parse_qs

import httpx2
import pytest
from shared_errors import InfrastructureError

from shared_auth.infrastructure.clients.client_credentials_token_provider import (
    ClientCredentialsTokenProvider,
)
from shared_auth.infrastructure.clients.exceptions import DownstreamError
from tests.fixtures.clients import (
    CLIENT_ID,
    CLIENT_SECRET,
    ISSUER_SERVICE,
    TARGET_AUDIENCE,
    TOKEN_ENDPOINT_URL,
    FakeClock,
    FakeTokenEndpoint,
    Handler,
)
from tests.fixtures.factory import READ_SCOPE, WRITE_SCOPE, build_error_response

MakeProvider = Callable[[Handler], ClientCredentialsTokenProvider]


class TestRequest:
    def test_sends_client_credentials(
        self, make_token_provider: MakeProvider, token_endpoint: FakeTokenEndpoint
    ) -> None:
        token: str = make_token_provider(token_endpoint).get_token()

        assert token == "service-token-1"
        request: httpx2.Request = token_endpoint.requests[0]
        assert request.method == "POST"
        assert str(request.url) == TOKEN_ENDPOINT_URL

    def test_authenticates_with_http_basic(
        self, make_token_provider: MakeProvider, token_endpoint: FakeTokenEndpoint
    ) -> None:
        # client_secret_basic (RFC 6749 §2.3.1): never in the form body.
        make_token_provider(token_endpoint).get_token()

        request: httpx2.Request = token_endpoint.requests[0]
        credentials: bytes = f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
        assert request.headers["Authorization"] == (
            f"Basic {base64.b64encode(credentials).decode()}"
        )
        assert CLIENT_SECRET not in request.content.decode()

    def test_sends_a_form_with_the_grant_audience_and_sorted_scopes(
        self, make_token_provider: MakeProvider, token_endpoint: FakeTokenEndpoint
    ) -> None:
        make_token_provider(token_endpoint).get_token()

        request: httpx2.Request = token_endpoint.requests[0]
        assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert parse_qs(request.content.decode()) == {
            "grant_type": ["client_credentials"],
            "audience": [TARGET_AUDIENCE],
            # RFC 6749 §3.3: one space-separated string. TARGET_SCOPES is
            # (write, read): the provider sorts them.
            "scope": [f"{READ_SCOPE} {WRITE_SCOPE}"],
        }


class TestCaching:
    def test_reuses_the_token_while_it_is_fresh(
        self,
        make_token_provider: MakeProvider,
        token_endpoint: FakeTokenEndpoint,
        clock: FakeClock,
    ) -> None:
        provider: ClientCredentialsTokenProvider = make_token_provider(token_endpoint)

        first: str = provider.get_token()
        clock.advance(269)  # 300 s lifetime, renewed 30 s before: still fresh
        second: str = provider.get_token()

        assert first == second
        assert len(token_endpoint.requests) == 1

    def test_renews_shortly_before_expiry(
        self,
        make_token_provider: MakeProvider,
        token_endpoint: FakeTokenEndpoint,
        clock: FakeClock,
    ) -> None:
        provider: ClientCredentialsTokenProvider = make_token_provider(token_endpoint)

        provider.get_token()
        clock.advance(270)  # 300 - RENEW_MARGIN_SECONDS
        renewed: str = provider.get_token()

        assert renewed == "service-token-2"
        assert len(token_endpoint.requests) == 2

    def test_a_short_lifetime_is_not_refetched_on_every_call(
        self, make_token_provider: MakeProvider, clock: FakeClock
    ) -> None:
        # Lifetime 20 s < 30 s margin: renew after half the lifetime instead.
        token_endpoint = FakeTokenEndpoint(expires_in=20)
        provider: ClientCredentialsTokenProvider = make_token_provider(token_endpoint)

        provider.get_token()
        clock.advance(9)
        provider.get_token()
        assert len(token_endpoint.requests) == 1

        clock.advance(1)  # 10 s = half of 20 s
        provider.get_token()
        assert len(token_endpoint.requests) == 2

    def test_concurrent_callers_share_one_request(
        self, make_token_provider: MakeProvider, token_endpoint: FakeTokenEndpoint
    ) -> None:
        token_endpoint.delay = 0.05  # slow endpoint: every thread arrives meanwhile
        provider: ClientCredentialsTokenProvider = make_token_provider(token_endpoint)
        tokens: list[str] = []

        threads: list[threading.Thread] = [
            threading.Thread(target=lambda: tokens.append(provider.get_token()))
            for _ in range(10)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(token_endpoint.requests) == 1
        assert tokens == ["service-token-1"] * 10


class TestErrors:
    def test_wrong_secret_becomes_downstream_error(
        self, make_token_provider: MakeProvider
    ) -> None:
        provider: ClientCredentialsTokenProvider = make_token_provider(
            lambda _request: build_error_response(401, "INVALID_CLIENT")
        )

        with pytest.raises(DownstreamError) as error:
            provider.get_token()

        # Named after the issuer given to the provider (for the logs).
        assert error.value.service == ISSUER_SERVICE
        assert error.value.downstream_code == "INVALID_CLIENT"

    def test_endpoint_down_becomes_infrastructure_error(
        self, make_token_provider: MakeProvider
    ) -> None:
        def handler(request: httpx2.Request) -> httpx2.Response:
            raise httpx2.ConnectError("refused", request=request)

        with pytest.raises(InfrastructureError):
            make_token_provider(handler).get_token()

    def test_endpoint_timeout_becomes_infrastructure_error(
        self, make_token_provider: MakeProvider
    ) -> None:
        def handler(request: httpx2.Request) -> httpx2.Response:
            raise httpx2.ReadTimeout("too slow", request=request)

        with pytest.raises(InfrastructureError):
            make_token_provider(handler).get_token()

    def test_endpoint_answering_503_becomes_infrastructure_error(
        self, make_token_provider: MakeProvider
    ) -> None:
        with pytest.raises(InfrastructureError):
            make_token_provider(lambda _request: httpx2.Response(503)).get_token()

    @pytest.mark.parametrize(
        "response",
        [
            httpx2.Response(200, text="not json"),
            httpx2.Response(200, json={"access_token": "t"}),  # no expires_in
            httpx2.Response(
                200,
                json={"access_token": "t", "token_type": "Bearer", "expires_in": "soon"},
            ),
        ],
    )
    def test_malformed_response_becomes_infrastructure_error(
        self, make_token_provider: MakeProvider, response: httpx2.Response
    ) -> None:
        with pytest.raises(InfrastructureError):
            make_token_provider(lambda _request: response).get_token()

    def test_a_failed_renewal_is_retried_on_the_next_call(
        self,
        make_token_provider: MakeProvider,
        token_endpoint: FakeTokenEndpoint,
        clock: FakeClock,
    ) -> None:
        endpoint_is_down: bool = False

        def handler(request: httpx2.Request) -> httpx2.Response:
            if endpoint_is_down:
                raise httpx2.ConnectError("refused", request=request)
            return token_endpoint(request)

        provider: ClientCredentialsTokenProvider = make_token_provider(handler)
        provider.get_token()
        clock.advance(300)

        endpoint_is_down = True
        with pytest.raises(InfrastructureError):
            provider.get_token()

        endpoint_is_down = False
        assert provider.get_token() == "service-token-2"

    def test_the_secret_is_not_in_repr(
        self, make_token_provider: MakeProvider, token_endpoint: FakeTokenEndpoint
    ) -> None:
        provider: ClientCredentialsTokenProvider = make_token_provider(token_endpoint)

        assert CLIENT_SECRET not in repr(provider._client_secret)
