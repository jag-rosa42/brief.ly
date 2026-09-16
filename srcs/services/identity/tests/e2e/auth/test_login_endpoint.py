from uuid import uuid4

from fastapi.testclient import TestClient
from httpx2 import Response


class TestLoginEndpoint:
    VALID_EMAIL: str = f"john.doe-{uuid4()}@example.com"
    VALID_PASSWORD: str = "super-secret"

    def test_login_returns_access_token_for_registered_account(
        self,
        client: TestClient,
    ) -> None:

        register_response: Response = client.post(
            "/api/auth/register",
            json={
                "email": self.VALID_EMAIL,
                "password": self.VALID_PASSWORD,
            },
        )

        assert register_response.status_code == 201

        login_response: Response = client.post(
            "/api/auth/login",
            json={
                "email": self.VALID_EMAIL,
                "password": self.VALID_PASSWORD,
            },
        )

        assert login_response.status_code == 200

        body: dict[str, str] = login_response.json()

        assert body["token_type"] == "Bearer"
        assert body["access_token"]

    def test_login_rejects_invalid_password(
        self,
        client: TestClient,
    ) -> None:
        register_response: Response = client.post(
            "/api/auth/register",
            json={
                "email": self.VALID_EMAIL,
                "password": self.VALID_PASSWORD,
            },
        )

        assert register_response.status_code == 201

        login_response: Response = client.post(
            "/api/auth/login",
            json={
                "email": self.VALID_EMAIL,
                "password": "wrong-password",
            },
        )

        assert login_response.status_code == 401
