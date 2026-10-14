from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_errors import ErrorResponse

from src.api.dependencies.security import (
    ANTI_CSRF_HEADER_NAME,
    get_refresh_account_session,
)
from src.domain.exception import (
    DomainError,
    InvalidTokenError,
    TokenExpiredError,
    TokenRevokedError,
)
from src.main import app
from tests import routes
from tests.fixtures.cookies import (
    REFRESH_COOKIE_PATH,
    cookie_session_headers,
    get_refresh_cookie,
)
from tests.fixtures.sessions import FakeRefreshAccountSession, build_account_session

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
    def test_returns_200_with_the_new_access_token(
        self,
        client: TestClient,
        use_refresh_account_session,
    ) -> None:
        fake = FakeRefreshAccountSession()
        use_refresh_account_session(fake)

        response: Response = client.post(
            url=routes.REFRESH,
            headers=cookie_session_headers(REFRESH_TOKEN),
        )

        assert response.status_code == 200
        # The refresh token is never in the body: only in the HttpOnly cookie.
        assert response.json() == {
            "access_token": "fake-access-token",
            "token_type": "Bearer",
        }
        # The use case receives the token read from the cookie.
        assert fake._execute_called_with == REFRESH_TOKEN

    def test_rotates_the_refresh_token_cookie(
        self,
        client: TestClient,
        use_refresh_account_session,
    ) -> None:
        fake = FakeRefreshAccountSession(
            build_account_session(refresh_token="rotated-refresh-token")
        )
        use_refresh_account_session(fake)

        response: Response = client.post(
            url=routes.REFRESH,
            headers=cookie_session_headers(REFRESH_TOKEN),
        )

        cookie = get_refresh_cookie(response)
        assert cookie.value == "rotated-refresh-token"
        assert cookie["httponly"] is True
        assert cookie["secure"] is True
        assert cookie["samesite"] == "strict"
        assert cookie["path"] == REFRESH_COOKIE_PATH

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
        use_refresh_account_session(FakeRefreshAccountSession(error=error))

        response: Response = client.post(
            url=routes.REFRESH,
            headers=cookie_session_headers(REFRESH_TOKEN),
        )

        assert response.status_code == 401
        assert "set-cookie" not in response.headers

    def test_returns_401_without_the_refresh_token_cookie(
        self,
        client: TestClient,
        use_refresh_account_session,
    ) -> None:
        fake = FakeRefreshAccountSession()
        use_refresh_account_session(fake)

        response: Response = client.post(
            url=routes.REFRESH,
            headers=cookie_session_headers(refresh_token=None),
        )

        assert response.status_code == 401
        body: ErrorResponse = ErrorResponse.model_validate(response.json())
        assert body.error.code == "INVALID_TOKEN"
        assert fake._execute_called_with is None

    @pytest.mark.parametrize(
        "headers",
        [
            cookie_session_headers(REFRESH_TOKEN, csrf=False),  # header missing
            {
                **cookie_session_headers(REFRESH_TOKEN, csrf=False),
                ANTI_CSRF_HEADER_NAME: "mobile",  # wrong value
            },
            {
                **cookie_session_headers(REFRESH_TOKEN, csrf=False),
                "X-Requested-With": "fetch",  # the old header is not accepted
            },
        ],
        ids=["missing", "wrong-value", "old-header"],
    )
    def test_returns_403_without_the_csrf_header(
        self,
        client: TestClient,
        use_refresh_account_session,
        headers: dict[str, str],
    ) -> None:
        fake = FakeRefreshAccountSession()
        use_refresh_account_session(fake)

        response: Response = client.post(url=routes.REFRESH, headers=headers)

        assert response.status_code == 403
        body: ErrorResponse = ErrorResponse.model_validate(response.json())
        assert body.error.code == "CSRF_CHECK_FAILED"
        # The session must not be touched: no rotation, no new cookie.
        assert fake._execute_called_with is None
        assert "set-cookie" not in response.headers

    def test_csrf_check_runs_before_the_cookie_check(
        self,
        client: TestClient,
        use_refresh_account_session,
    ) -> None:
        # Neither header nor cookie: the guard answers first (403, not 401).
        use_refresh_account_session(FakeRefreshAccountSession())

        response: Response = client.post(url=routes.REFRESH)

        assert response.status_code == 403

    def test_ignores_a_refresh_token_sent_in_the_body(
        self,
        client: TestClient,
        use_refresh_account_session,
    ) -> None:
        # The old contract (token in the JSON body) must no longer work.
        fake = FakeRefreshAccountSession()
        use_refresh_account_session(fake)

        response: Response = client.post(
            url=routes.REFRESH,
            headers=cookie_session_headers(refresh_token=None),
            json={"refresh_token": REFRESH_TOKEN},
        )

        assert response.status_code == 401
        assert fake._execute_called_with is None
