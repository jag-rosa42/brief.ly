from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_errors import ErrorResponse

from src.api.dependencies.account import get_login_account
from src.domain.exception import InvalidCredentialsError
from src.infrastructure.security.settings import security_settings
from src.main import app
from tests import routes
from tests.fixtures.accounts import FakeLoginAccount
from tests.fixtures.cookies import REFRESH_COOKIE_PATH, get_refresh_cookie

VALID_EMAIL: str = "john.doe@example.com"
VALID_PASSWORD: str = "super-secret"


@pytest.fixture
def client() -> TestClient:
    """
    TestClient without database dependency overrides.

    This fixture shadows the conftest client fixture for tests
    that do not require database access.
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def use_login_account() -> Generator:
    def _use(fake_use_case: FakeLoginAccount) -> None:
        app.dependency_overrides[get_login_account] = lambda: fake_use_case

    yield _use
    app.dependency_overrides.pop(get_login_account, None)


class TestAuthLoginAccount:
    def test_returns_200_on_login_success(
        self,
        client: TestClient,
        use_login_account,
    ) -> None:
        fake_login_account: FakeLoginAccount = FakeLoginAccount()
        use_login_account(fake_login_account)

        response: Response = client.post(
            url=routes.LOGIN,
            json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        )

        assert response.status_code == 200
        assert response.json() == {
            "access_token": "fake-access-token",
            "token_type": "Bearer",
        }
        assert fake_login_account._execute_called_with == (
            VALID_EMAIL,
            VALID_PASSWORD,
        )

    def test_returns_401_when_credentials_are_invalid(
        self,
        client: TestClient,
        use_login_account,
    ) -> None:
        fake_login_account: FakeLoginAccount = FakeLoginAccount(
            error=InvalidCredentialsError()
        )
        use_login_account(fake_login_account)

        response: Response = client.post(
            url=routes.LOGIN,
            json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        )

        assert response.status_code == 401
        body: ErrorResponse = ErrorResponse.model_validate(response.json())
        assert body.error.code == "INVALID_CREDENTIALS"
        assert "set-cookie" not in response.headers

    @pytest.mark.parametrize(
        "body",
        [
            {"password": "super-secret"},  # missing email case
            {"email": "john.doe@example.com"},  # missing password case
            {"email": "not-an-email", "password": "super-secret"},  # unvalid body
            {},  # empty body case
        ],
    )
    def test_returns_422_on_invalid_request_body(
        self,
        client: TestClient,
        body: dict[str, str],
    ) -> None:
        response: Response = client.post(
            url=routes.LOGIN,
            json=body,
        )

        assert response.status_code == 422

    def test_sets_the_refresh_token_cookie(
        self,
        client: TestClient,
        use_login_account,
    ) -> None:
        use_login_account(FakeLoginAccount())

        response: Response = client.post(
            url=routes.LOGIN,
            json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        )

        cookie = get_refresh_cookie(response)
        assert cookie.value == "fake-refresh-token"
        assert cookie["httponly"] is True
        assert cookie["secure"] is True
        assert cookie["samesite"] == "strict"
        assert cookie["path"] == REFRESH_COOKIE_PATH
        # The cookie lives exactly as long as the refresh token itself.
        # Compared to the settings, not to a literal, so a local .env with
        # another lifetime does not break the test.
        expected_max_age: int = security_settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        assert cookie["max-age"] == str(expected_max_age)


    def test_does_not_require_the_csrf_header(
        self,
        client: TestClient,
        use_login_account,
    ) -> None:
        # login only SETS the cookie: it is not on the guarded router.
        use_login_account(FakeLoginAccount())

        response: Response = client.post(
            url=routes.LOGIN,
            json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        )

        assert response.status_code == 200