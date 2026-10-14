from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_errors import ErrorResponse

from src.api.dependencies.account import get_login_account
from src.domain.exception import InvalidCredentialsError
from src.main import app
from tests import routes
from tests.fixtures.accounts import FakeLoginAccount

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
            "refresh_token": "fake-refresh-token",
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
