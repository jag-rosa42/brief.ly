from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from src.api.dependencies.account import get_current_account
from src.domain.entities.account import Account
from src.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def use_current_account():
    def _use(account: Account) -> None:
        app.dependency_overrides[get_current_account] = lambda: account

    yield _use

    app.dependency_overrides.pop(get_current_account, None)


class TestAccountsRouter:
    def test_returns_current_account(
        self,
        client: TestClient,
        account: Account,
        use_current_account,
    ) -> None:
        use_current_account(account)

        response: Response = client.get("/api/accounts/me")

        assert response.status_code == 200

        body = response.json()

        assert body["id"] == str(account.id)
        assert body["email"] == account.email.value
        assert datetime.fromisoformat(body["created_at"]) == account.created_at

    def test_returns_401_with_invalid_access_token(
        self,
        client: TestClient,
    ) -> None:
        response: Response = client.get(
            url="/api/accounts/me",
            headers={"Authorization": "Bearer not-a-jwt"}
        )

        assert response.status_code == 401

    def test_rejetcs_a_request_without_credentials(
        self,
        client: TestClient,
    ) -> None:
        response: Response = client.get("/api/accounts/me")

        assert response.status_code == 401