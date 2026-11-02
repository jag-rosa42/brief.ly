"""
FakeTokenIssuer, used the way a service's tests would use it: the app is
built with its real settings, then told to trust the fake issuer instead.
"""

from collections.abc import Generator
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response

from shared_auth.domain.token_type import TokenType
from shared_auth.infrastructure.settings import AuthSettings
from shared_auth.testing import FakeTokenIssuer
from tests.fixtures.factory import (
    ACCESS_AUDIENCE,
    ACCOUNT_ID,
    ISSUER,
    OTHER_SERVICE_AUDIENCE,
    PUBLIC_API_AUDIENCE,
    READ_SCOPE,
    SERVICE_AUDIENCE,
    SERVICE_NAME,
    WRITE_SCOPE,
)
from tests.fixtures.http import Routes, build_test_app, error_code


@pytest.fixture(scope="module")
def issuer() -> FakeTokenIssuer:
    return FakeTokenIssuer(
        issuer=ISSUER,
        access_audience=ACCESS_AUDIENCE,
        public_api_audience=PUBLIC_API_AUDIENCE,
    )


@pytest.fixture
def app(auth_settings: AuthSettings, issuer: FakeTokenIssuer) -> Generator[FastAPI]:
    app: FastAPI = build_test_app(auth_settings)
    issuer.override_authenticator(app, service_audience=SERVICE_AUDIENCE, public_api=True)
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestFakeTokenIssuer:
    def test_user_token(self, client: TestClient, issuer: FakeTokenIssuer) -> None:
        token: str = issuer.user_token(ACCOUNT_ID)

        response: Response = client.get(Routes.USER, headers=issuer.bearer(token))

        assert response.status_code == 200
        assert response.json() == {"account_id": str(ACCOUNT_ID)}

    def test_expired_user_token(
        self, client: TestClient, issuer: FakeTokenIssuer
    ) -> None:
        token: str = issuer.user_token(ACCOUNT_ID, expires_in=timedelta(seconds=-1))

        response: Response = client.get(Routes.USER, headers=issuer.bearer(token))

        assert response.status_code == 401
        assert error_code(response) == "TOKEN_EXPIRED"

    def test_service_token_with_the_scope(
        self, client: TestClient, issuer: FakeTokenIssuer
    ) -> None:
        token: str = issuer.service_token(
            SERVICE_NAME, audience=SERVICE_AUDIENCE, scopes=[WRITE_SCOPE]
        )

        response: Response = client.post(
            Routes.SCOPED_SERVICE, headers=issuer.bearer(token)
        )

        assert response.status_code == 200
        assert response.json() == {"service": SERVICE_NAME}

    def test_service_token_for_another_service(
        self, client: TestClient, issuer: FakeTokenIssuer
    ) -> None:
        token: str = issuer.service_token(SERVICE_NAME, audience=OTHER_SERVICE_AUDIENCE)

        response: Response = client.get(Routes.SERVICE, headers=issuer.bearer(token))

        assert response.status_code == 401

    def test_public_api_token_without_the_scope(
        self, client: TestClient, issuer: FakeTokenIssuer
    ) -> None:
        token: str = issuer.public_api_token(ACCOUNT_ID, scopes=[READ_SCOPE])

        response: Response = client.post(
            Routes.SCOPED_PUBLIC_USER, headers=issuer.bearer(token)
        )

        assert response.status_code == 403
        assert error_code(response) == "INSUFFICIENT_SCOPE"

    def test_any_token_for_unusual_cases(
        self, client: TestClient, issuer: FakeTokenIssuer
    ) -> None:
        token: str = issuer.token(
            subject=str(ACCOUNT_ID),
            token_type=TokenType.REFRESH,
            audience=ACCESS_AUDIENCE,
        )

        response: Response = client.get(Routes.USER, headers=issuer.bearer(token))

        assert response.status_code == 401
        assert error_code(response) == "INVALID_TOKEN"

    def test_default_values_match_the_settings_defaults(self) -> None:
        # Services use these defaults: their tokens must match out of the box.
        issuer = FakeTokenIssuer()
        defaults = AuthSettings(
            _env_file=None,
            JWT_PUBLIC_KEY=issuer.public_key_pem,
            JWT_SERVICE_AUDIENCE=SERVICE_AUDIENCE,
        )

        assert issuer.issuer == defaults.JWT_ISSUER
        assert issuer.access_audience == defaults.JWT_ACCESS_AUDIENCE
