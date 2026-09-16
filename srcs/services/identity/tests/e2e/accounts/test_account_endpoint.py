from uuid import uuid4

from fastapi.testclient import TestClient
from httpx2 import Response


class TestAccountsEndpoints:
    def test_returns_accounts_with_valid_access_token(
        self,
        client: TestClient,
    ) -> None:
        email: str = f"john.doe-{uuid4()}@example.com"
        password: str = "super-secret"

        registered_account_response: Response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

        assert registered_account_response.status_code == 201

        login_response = client.post(
            url="/api/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert login_response.status_code == 200

        access_token = login_response.json()["access_token"]

        protected_response: Response = client.get(
            url="/api/accounts/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert protected_response.status_code == 200
        body: dict[str, str] = protected_response.json()

        assert body["id"] == registered_account_response.json()["id"]
        assert body["email"] == email
        assert body["created_at"]
