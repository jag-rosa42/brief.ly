from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_errors import ErrorResponse

from src.api.dependencies.account import get_register_account
from src.domain.exception import EmailAlreadyRegisteredError
from src.main import app
from tests import routes
from tests.fixtures.accounts import FakeRegisterAccount
from tests.fixtures.cookies import REFRESH_COOKIE_PATH, get_refresh_cookie
from tests.fixtures.sessions import build_account_session

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
def use_register_account() -> Generator:

    def _use(fake_use_case: FakeRegisterAccount) -> None:
        app.dependency_overrides[get_register_account] = lambda: fake_use_case

    yield _use
    app.dependency_overrides.pop(get_register_account, None)


class TestAuthRegisterRouter:
    def test_returns_201_on_register_account_success(
        self,
        client: TestClient,
        use_register_account,
    ) -> None:
        fake_register_account: FakeRegisterAccount = FakeRegisterAccount(
            build_account_session(
                access_token="test-access-token",
                refresh_token="test-refresh-token",
            )
        )
        use_register_account(fake_register_account)

        response: Response = client.post(
            url=routes.REGISTER,
            json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        )

        assert response.status_code == 201
        assert response.json() == {
            "access_token": "test-access-token",
            "token_type": "Bearer",
        }

        cookie = get_refresh_cookie(response)
        assert cookie.value == "test-refresh-token"
        assert cookie["httponly"] is True
        assert cookie["secure"] is True
        assert cookie["samesite"] == "strict"
        assert cookie["path"] == REFRESH_COOKIE_PATH

        assert fake_register_account._execute_called_with == (
            VALID_EMAIL,
            VALID_PASSWORD,
        )

    def test_returns_409_when_email_already_registered(
        self,
        client: TestClient,
        use_register_account,
    ) -> None:
        fake_register_account: FakeRegisterAccount = FakeRegisterAccount(
            error=EmailAlreadyRegisteredError()
        )
        use_register_account(fake_register_account)

        response: Response = client.post(
            url=routes.REGISTER,
            json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        )

        assert response.status_code == 409
        body: ErrorResponse = ErrorResponse.model_validate(response.json())
        assert body.error.code == "EMAIL_ALREADY_REGISTERED"

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
        response: Response = client.post(routes.REGISTER, json=body)

        assert response.status_code == 422
