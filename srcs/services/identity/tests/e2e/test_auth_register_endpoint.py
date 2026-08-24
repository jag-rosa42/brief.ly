from fastapi.testclient import TestClient
from httpx2 import Response


class TestAuthResgiterEndpoint:
    def test_duplicate_registration_is_rejected(self, client: TestClient):
        email: str = "john.doe@example.com"
        register_response: Response = client.post(
            "/api/auth/register", json={"email": email, "password": "super-secret"}
        )

        assert register_response.status_code == 201
        assert register_response.json()["email"] == email

        duplicated_response = client.post(
            "/api/auth/register",
            json={"email": email, "password": "another-super-secret"},
        )

        assert duplicated_response.status_code == 409
