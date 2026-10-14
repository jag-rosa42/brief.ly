from concurrent.futures import ThreadPoolExecutor
from concurrent.futures._base import Future
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx2 import Response

from tests import routes
from tests.fixtures.cookies import get_refresh_cookie


class TestRegisterEndpoint:
    def test_duplicate_registration_is_rejected(self, client: TestClient) -> None:
        email: str = "john.doe@example.com"

        register_response: Response = client.post(
            url=routes.REGISTER,
            json={"email": email, "password": "super-secret"},
        )

        assert register_response.status_code == 201
        body = register_response.json()
        assert body["access_token"]
        assert "refresh-token" not in body
        assert body["token_type"] == "Bearer"
        assert get_refresh_cookie(register_response).value

        duplicated_response = client.post(
            url=routes.REGISTER,
            json={"email": email, "password": "another-super-secret"},
        )

        assert duplicated_response.status_code == 409

    def test_concurrent_registration_with_same_email(
        self,
        concurrent_clients: tuple[TestClient, TestClient],
    ) -> None:
        """
        Concurrent registrations for the same email result in one success
        and one conflict.
        """
        client_a, client_b = concurrent_clients

        email = f"john.doe{uuid4()}@example.com"
        payload: dict[str, str] = {
            "email": email,
            "password": "super-secret",
        }

        def register(client: TestClient) -> int:
            response: Response = client.post(
                url=routes.REGISTER,
                json=payload,
            )
            return response.status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures: list[Future[int]] = [
                executor.submit(register, client_a),
                executor.submit(register, client_b),
            ]

            status_codes: list[int] = [future.result() for future in futures]

        assert sorted(status_codes) == [201, 409]
