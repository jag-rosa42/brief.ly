import datetime
from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from src.api.routers.auth.router import get_register_account
from src.domain.entities.account import Account
from src.domain.exception import DomainError, EmailAlreadyRegisteredError
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash
from src.main import app

VALID_EMAIL: str = "john.doe@example.com"
VALID_PASSWORD: str = "super-secret"


class FakeRegisterAccount:
    def __init__(self, account: Account, error: DomainError | None = None) -> None:
        self._account: Account = account
        self._error: DomainError | None = error
        self.execute_called_with: tuple[str, str] | None = None

    def execute(self, email: str, password: str) -> Account:
        self.execute_called_with: tuple[str, str] = email, password
        if self._error is not None:
            raise self._error
        return self._account


def _build_account(email: str = VALID_EMAIL, password: str = VALID_PASSWORD) -> Account:
    return Account(
        id=uuid4(),
        email=Email(email),
        password_hash=PasswordHash(password),
        created_at=datetime.datetime.now(datetime.UTC),
    )


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
        self, client: TestClient, use_register_account
    ) -> None:
        account: Account = _build_account()
        fake_register_account: FakeRegisterAccount = FakeRegisterAccount(account)
        use_register_account(fake_register_account)

        response: Response = client.post(
            "/api/auth/register",
            json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        )

        assert response.status_code == 201
        assert response.json() == {"id": str(account.id), "email": VALID_EMAIL}
        assert fake_register_account.execute_called_with == (
            VALID_EMAIL,
            VALID_PASSWORD,
        )

    def test_returns_409_when_email_already_registered(
        self, client: TestClient, use_register_account
    ) -> None:
        account: Account = _build_account()
        fake_register_account: FakeRegisterAccount = FakeRegisterAccount(
            account, EmailAlreadyRegisteredError()
        )
        use_register_account(fake_register_account)

        response: Response = client.post(
            "/api/auth/register",
            json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        )

        assert response.status_code == 409
        assert response.json() == {"detail": "Email already registered"}

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
        self, client: TestClient, body: dict[str, str]
    ) -> None:
        response: Response = client.post("/api/auth/register", json=body)

        assert response.status_code == 422
