from uuid import uuid4

from fastapi.testclient import TestClient
from httpx2 import Response

from tests import routes


class TestAccountsEndpoints:
    def test_returns_accounts_with_access_token_from_register(
        self,
        client: TestClient,
    ) -> None:
        email: str = f"john.doe-{uuid4()}@example.com"
        password: str = "super-secret"

        registered_account_response: Response = client.post(
            routes.REGISTER,
            json={"email": email, "password": password},
        )

        assert registered_account_response.status_code == 201
        access_token: str = registered_account_response.json()["access_token"]

        protected_response: Response = client.get(
            url=routes.ACCOUNTS_ME,
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert protected_response.status_code == 200
        body: dict[str, str] = protected_response.json()

        assert body["email"] == email
        assert body["created_at"]

    def test_returns_account_with_access_token_from_login(
        self,
        client: TestClient,
    ) -> None:
        email: str = f"john.doe-{uuid4()}@example.com"
        password: str = "super-secret"

        client.post(routes.REGISTER, json={"email": email, "password": password})

        login_response: Response = client.post(
            routes.LOGIN,
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200
        access_token: str = login_response.json()["access_token"]

        protected_response: Response = client.get(
            routes.ACCOUNTS_ME,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert protected_response.status_code == 200
        assert protected_response.json()["email"] == email

    def test_rejects_an_invalid_access_token(self, client: TestClient) -> None:
        response: Response = client.get(
            routes.ACCOUNTS_ME,
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert response.status_code == 401

    def test_rejects_a_missing_access_token(self, client: TestClient) -> None:
        response: Response = client.get(routes.ACCOUNTS_ME)
        assert response.status_code == 401
