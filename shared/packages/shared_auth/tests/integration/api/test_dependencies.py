"""
The FastAPI dependencies, through the test app (tests/fixtures/http.py):
real requests, real error format.
"""

from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response

from shared_auth.api.dependencies import CurrentUserDep
from shared_auth.infrastructure.settings import AuthSettings
from tests.fixtures.factory import (
    ACCOUNT_ID,
    PUBLIC_API_AUDIENCE,
    READ_SCOPE,
    REFRESH_AUDIENCE,
    SERVICE_NAME,
    WRITE_SCOPE,
)
from tests.fixtures.http import Routes, bearer, build_test_app, error_code
from tests.fixtures.security import TokenFactory


class TestStartup:
    def test_an_invalid_public_key_fails_at_startup(
        self, auth_settings: AuthSettings
    ) -> None:
        settings = auth_settings.model_copy(update={"JWT_PUBLIC_KEY": "not a key"})

        with pytest.raises(ValueError):
            build_test_app(settings)

    def test_a_route_without_installed_authentication_fails_loudly(self) -> None:
        app = FastAPI()

        @app.get(Routes.USER)
        def user_route(user: CurrentUserDep) -> None: ...

        with pytest.raises(RuntimeError, match="install_authentication"):
            TestClient(app).get(Routes.USER, headers=bearer("anything"))


class TestCurrentUser:
    def test_returns_the_user(self, client: TestClient, make_token: TokenFactory) -> None:
        response: Response = client.get(Routes.USER, headers=bearer(make_token()))

        assert response.status_code == 200
        assert response.json() == {"account_id": str(ACCOUNT_ID)}

    def test_401_without_a_token(self, client: TestClient) -> None:
        response: Response = client.get(Routes.USER)

        assert response.status_code == 401
        assert error_code(response) == "INVALID_TOKEN"
        # RFC 6750 §3: a 401 on a bearer-protected route names the scheme.
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_401_with_another_scheme(self, client: TestClient) -> None:
        response: Response = client.get(
            Routes.USER, headers={"Authorization": "Basic abc"}
        )

        assert response.status_code == 401
        assert error_code(response) == "INVALID_TOKEN"

    def test_401_token_expired(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        token: str = make_token(
            issued_ago=timedelta(minutes=20), expires_in=timedelta(minutes=15)
        )

        response: Response = client.get(Routes.USER, headers=bearer(token))

        assert response.status_code == 401
        # The frontend refreshes on exactly this code.
        assert error_code(response) == "TOKEN_EXPIRED"

    def test_401_with_a_refresh_token(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        token: str = make_token(overrides={"type": "refresh", "aud": REFRESH_AUDIENCE})

        response: Response = client.get(Routes.USER, headers=bearer(token))

        assert response.status_code == 401
        assert error_code(response) == "INVALID_TOKEN"

    def test_401_with_a_service_token(
        self, client: TestClient, service_token: TokenFactory
    ) -> None:
        response: Response = client.get(Routes.USER, headers=bearer(service_token()))

        assert response.status_code == 401


class TestCurrentForwardedUser:
    def test_browser_token_forwarded(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        response: Response = client.get(
            Routes.FORWARDED_USER, headers=bearer(make_token())
        )

        assert response.status_code == 200
        assert response.json() == {"account_id": str(ACCOUNT_ID)}

    def test_public_api_token_forwarded(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        token: str = make_token(
            overrides={"aud": PUBLIC_API_AUDIENCE, "scope": READ_SCOPE}
        )

        response: Response = client.get(Routes.FORWARDED_USER, headers=bearer(token))

        assert response.status_code == 200

    def test_401_with_a_service_token(
        self, client: TestClient, service_token: TokenFactory
    ) -> None:
        response: Response = client.get(
            Routes.FORWARDED_USER, headers=bearer(service_token())
        )

        assert response.status_code == 401
        assert error_code(response) == "INVALID_TOKEN"


class TestCurrentService:
    def test_returns_the_service(
        self, client: TestClient, service_token: TokenFactory
    ) -> None:
        response: Response = client.get(Routes.SERVICE, headers=bearer(service_token()))

        assert response.status_code == 200
        assert response.json() == {"service": SERVICE_NAME}

    def test_401_with_a_user_token(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        response: Response = client.get(Routes.SERVICE, headers=bearer(make_token()))

        assert response.status_code == 401


class TestRequiredServiceScopes:
    def test_service_with_the_scope(
        self, client: TestClient, service_token: TokenFactory
    ) -> None:
        response: Response = client.post(
            Routes.SCOPED_SERVICE, headers=bearer(service_token(WRITE_SCOPE))
        )

        assert response.status_code == 200

    def test_403_service_without_the_scope(
        self, client: TestClient, service_token: TokenFactory
    ) -> None:
        response: Response = client.post(
            Routes.SCOPED_SERVICE, headers=bearer(service_token(READ_SCOPE))
        )

        assert response.status_code == 403
        assert error_code(response) == "INSUFFICIENT_SCOPE"
        assert "WWW-Authenticate" not in response.headers

    def test_401_user_where_a_service_scope_is_required(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        response: Response = client.post(
            Routes.SCOPED_SERVICE, headers=bearer(make_token())
        )

        assert response.status_code == 401


class TestRequiredPublicApiScopes:
    def test_public_api_token_with_the_scope(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        token: str = make_token(
            overrides={"aud": PUBLIC_API_AUDIENCE, "scope": f"{READ_SCOPE} {WRITE_SCOPE}"}
        )

        response: Response = client.post(Routes.SCOPED_PUBLIC_USER, headers=bearer(token))

        assert response.status_code == 200

    def test_403_public_api_token_without_the_scope(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        token: str = make_token(
            overrides={"aud": PUBLIC_API_AUDIENCE, "scope": READ_SCOPE}
        )

        response: Response = client.post(Routes.SCOPED_PUBLIC_USER, headers=bearer(token))

        assert response.status_code == 403
        assert error_code(response) == "INSUFFICIENT_SCOPE"

    def test_401_browser_token_on_the_public_api(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        response: Response = client.post(
            Routes.SCOPED_PUBLIC_USER, headers=bearer(make_token())
        )

        assert response.status_code == 401
