from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_errors import ErrorResponse

from src.api.dependencies.account import get_logout_account
from src.main import app
from tests import routes
from tests.fixtures.cookies import (
    REFRESH_COOKIE_PATH,
    cookie_session_headers,
    get_refresh_cookie,
)
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
def use_logout_account() -> Generator:
    def _use(fake_use_case: FakeRefreshAccountSession) -> None:
        app.dependency_overrides[get_logout_account] = lambda: fake_use_case

    yield _use
    app.dependency_overrides.pop(get_logout_account, None)


class TestAuthLogoutRouter:
    def test_returns_204_without_a_body(
        self,
        client: TestClient,
        use_logout_account,
    ) -> None:
        fake = FakeRefreshAccountSession()
        use_logout_account(fake)

        response: Response = client.post(
            url=routes.LOGOUT,
            headers=cookie_session_headers(REFRESH_TOKEN),
        )

        assert response.status_code == 204
        # response.content is returned as bytes.
        #  b"" is an empty bytes value
        assert response.content == b""
        # The use case receives the token read from the cookie.
        assert fake._execute_called_with == REFRESH_TOKEN

    def test_clears_the_refresh_token_cookie(
        self,
        client: TestClient,
        use_logout_account,
    ) -> None:
        use_logout_account(FakeRefreshAccountSession())

        response: Response = client.post(
            url=routes.LOGOUT,
            headers=cookie_session_headers(REFRESH_TOKEN),
        )

        # A cookie is deleted by setting it again, empty, already expired,
        # with the same name and path.
        cookie = get_refresh_cookie(response)
        assert cookie.value == ""
        assert cookie["max-age"] == "0"
        assert cookie["path"] == REFRESH_COOKIE_PATH

    def test_returns_204_and_clears_the_cookie_without_a_refresh_token(
        self,
        client: TestClient,
        use_logout_account,
    ) -> None:
        # Logout is idempotent: nothing to revoke, but still a success.
        fake = FakeRefreshAccountSession()
        use_logout_account(fake)

        response: Response = client.post(
            url=routes.LOGOUT,
            headers=cookie_session_headers(refresh_token=None),
        )

        assert response.status_code == 204
        assert fake._execute_called_with is None
        assert get_refresh_cookie(response)["max-age"] == "0"

    def test_returns_403_without_the_csrf_header(
        self,
        client: TestClient,
        use_logout_account,
    ) -> None:
        fake = FakeRefreshAccountSession()
        use_logout_account(fake)

        response: Response = client.post(
            url=routes.LOGOUT,
            headers=cookie_session_headers(REFRESH_TOKEN, csrf=False),
        )

        assert response.status_code == 403
        body: ErrorResponse = ErrorResponse.model_validate(response.json())
        assert body.error.code == "CSRF_CHECK_FAILED"
        # Nothing was revoked, and the cookie is left alone.
        assert fake._execute_called_with is None
        assert "set-cookie" not in response.headers
