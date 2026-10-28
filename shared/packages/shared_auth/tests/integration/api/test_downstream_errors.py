"""
End to end inside one service: a route calls another service on behalf of
the user, and the downstream failure reaches the caller with the right status
and code (a downstream TOKEN_EXPIRED stays TOKEN_EXPIRED, so the frontend
refreshes; a dead service becomes 503).
"""

from collections.abc import Callable

import httpx2
from fastapi.testclient import TestClient
from httpx2 import Response

from shared_auth.infrastructure.clients.downstream_client import DownstreamClient
from shared_auth.infrastructure.settings import AuthSettings
from tests.fixtures.clients import DOWNSTREAM_SERVICE, Handler
from tests.fixtures.factory import build_error_response
from tests.fixtures.http import Routes, bearer, build_test_app, error_code
from tests.fixtures.security import TokenFactory

MakeClient = Callable[[Handler], DownstreamClient]


class TestDownstreamErrorsReachTheCaller:
    def _call_downstream(
        self,
        auth_settings: AuthSettings,
        make_downstream_client: MakeClient,
        handler: Handler,
        token: str,
    ) -> Response:
        app = build_test_app(auth_settings, downstream=make_downstream_client(handler))
        # raise_server_exceptions=False: check the answer the caller really
        # gets, even if a handler is missing (a 500 instead of an exception).
        client = TestClient(app, raise_server_exceptions=False)
        return client.get(Routes.CALL_DOWNSTREAM, headers=bearer(token))

    def test_the_user_token_reaches_the_downstream_service(
        self,
        auth_settings: AuthSettings,
        make_downstream_client: MakeClient,
        make_token: TokenFactory,
    ) -> None:
        seen: list[str] = []

        def handler(request: httpx2.Request) -> httpx2.Response:
            seen.append(request.headers["Authorization"])
            return httpx2.Response(200, json=[{"id": 1}])

        token: str = make_token()
        response: Response = self._call_downstream(
            auth_settings, make_downstream_client, handler, token
        )

        assert response.status_code == 200
        assert response.json() == [{"id": 1}]
        assert seen == [f"Bearer {token}"]

    def test_downstream_token_expired_becomes_401_token_expired(
        self,
        auth_settings: AuthSettings,
        make_downstream_client: MakeClient,
        make_token: TokenFactory,
    ) -> None:
        response: Response = self._call_downstream(
            auth_settings,
            make_downstream_client,
            lambda _request: build_error_response(401, "TOKEN_EXPIRED"),
            make_token(),
        )

        assert response.status_code == 401
        assert error_code(response) == "TOKEN_EXPIRED"

    def test_dead_downstream_service_becomes_503(
        self,
        auth_settings: AuthSettings,
        make_downstream_client: MakeClient,
        make_token: TokenFactory,
    ) -> None:
        def handler(request: httpx2.Request) -> httpx2.Response:
            raise httpx2.ConnectError("name resolution failed", request=request)

        response: Response = self._call_downstream(
            auth_settings, make_downstream_client, handler, make_token()
        )

        assert response.status_code == 503
        assert error_code(response) == "SERVICE_UNAVAILABLE"

    def test_unexpected_downstream_error_becomes_502_without_details(
        self,
        auth_settings: AuthSettings,
        make_downstream_client: MakeClient,
        make_token: TokenFactory,
    ) -> None:
        response: Response = self._call_downstream(
            auth_settings,
            make_downstream_client,
            lambda _request: build_error_response(400, "VALIDATION_ERROR"),
            make_token(),
        )

        assert response.status_code == 502
        assert error_code(response) == "DOWNSTREAM_ERROR"
        # No internal topology in the answer: it is only logged.
        assert DOWNSTREAM_SERVICE not in response.text
