from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from src.api.dependencies.security import get_refresh_account_session
from src.domain.exception import (
    DomainError,
    InvalidTokenError,
    TokenExpiredError,
    TokenRevokedError,
)
from src.main import app
from tests import routes
from tests.fixtures.sessions import FakeRefreshAccountSession

REFRESH_TOKEN: str = "current-refresh-token"


@pytest.fixture
def client() -> TestClient:
    """
    TestClient without database dependency overrides.

    This fixture shadows the conftest client fixture for tests
    that do not require database access.
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def use_refresh_account_session() -> Generator:
    def _use(fake_use_case: FakeRefreshAccountSession) -> None:
        app.dependency_overrides[get_refresh_account_session] = lambda: fake_use_case

    yield _use
    app.dependency_overrides.pop(get_refresh_account_session, None)


class TestAuthRefreshRouter:
    def test_returns_200_with_the_new_session(
        self,
        client: TestClient,
        use_refresh_account_session,
    ) -> None:
        fake = FakeRefreshAccountSession()
        use_refresh_account_session(fake)

        response: Response = client.post(
            url=routes.REFRESH,
            json={"refresh_token": REFRESH_TOKEN},
        )

        assert response.status_code == 200
        assert response.json() == {
            "access_token": "fake-access-token",
            "refresh_token": "fake-refresh-token",
            "token_type": "Bearer",
        }

    @pytest.mark.parametrize(
        "error",
        [InvalidTokenError(), TokenExpiredError(), TokenRevokedError()],
    )
    def test_returns_401_when_the_refresh_token_is_rejected(
        self,
        client: TestClient,
        use_refresh_account_session,
        error: DomainError,
    ) -> None:
        fake = FakeRefreshAccountSession(error=error)
        use_refresh_account_session(fake)

        response: Response = client.post(
            url=routes.REFRESH,
            json={"refresh_token": REFRESH_TOKEN},
        )

        assert response.status_code == 401

    @pytest.mark.parametrize(
        "body",
        [
            {},
            {"refresh_token": None},
            {"refresh_token": 123},
            {"token": REFRESH_TOKEN},
        ],
    )
    def test_returns_422_on_invalid_request_body(
        self,
        client: TestClient,
        body: dict,
    ) -> None:
        response: Response = client.post(
            url=routes.REFRESH,
            json=body,
        )

        assert response.status_code == 422
