from fastapi.testclient import TestClient
from httpx2 import Response

from tests.fixtures.factory import DEFAULT_ACCOUNT_EMAIL, DEFAULT_ACCOUNT_PASSWORD

CREDENTIALS = {
    "email": DEFAULT_ACCOUNT_EMAIL,
    "password": DEFAULT_ACCOUNT_PASSWORD,
}


class TestAuthSessionFlow:
    def _register(self, client: TestClient) -> dict[str, str]:
        response: Response = client.post(
            "/api/auth/register",
            json=CREDENTIALS,
        )
        assert response.status_code == 201
        return response.json()

    def _refresh(self, client: TestClient, refresh_token: str) -> Response:
        return client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    def test_access_token_from_register_authenticates_me(
        self, client: TestClient
    ) -> None:
        session = self._register(client)

        response: Response = client.get(
            "/api/accounts/me",
            headers={"Authorization": f"Bearer {session['access_token']}"},
        )

        assert response.status_code == 200
        assert response.json()["email"] == DEFAULT_ACCOUNT_EMAIL

    def test_refresh_rotates_both_tokens(self, client: TestClient) -> None:
        initial_session = self._register(client)

        response = self._refresh(
            client,
            initial_session["refresh_token"],
        )

        assert response.status_code == 200
        refreshed_session = response.json()
        assert refreshed_session["refresh_token"] != initial_session["refresh_token"]
        assert refreshed_session["access_token"] != initial_session["access_token"]

    def test_reusing_a_rotated_token_revokes_the_whole_family(
        self, client: TestClient
    ) -> None:
        initial_session = self._register(client)
        refreshed_session = self._refresh(
            client,
            initial_session["refresh_token"],
        ).json()

        reused_token_response = self._refresh(client, initial_session["refresh_token"])
        newest_token_response = self._refresh(client, refreshed_session["refresh_token"])

        assert reused_token_response.status_code == 401
        assert (
            newest_token_response.status_code == 401
        )  # the newest token was revoked too

    def test_logout_revokes_the_refresh_token(self, client: TestClient) -> None:
        session = self._register(client)

        logout = client.post(
            "/api/auth/logout",
            json={"refresh_token": session["refresh_token"]},
        )

        assert logout.status_code == 204
        assert self._refresh(client, session["refresh_token"]).status_code == 401

    def test_logout_only_ends_that_session(self, client: TestClient) -> None:
        initial_session = self._register(client)
        refreshed_session = client.post(
            "/api/auth/login",
            json=CREDENTIALS,
        ).json()

        client.post(
            "/api/auth/logout", json={"refresh_token": initial_session["refresh_token"]}
        )

        assert (
            self._refresh(client, refreshed_session["refresh_token"]).status_code == 200
        )

    def test_retrying_a_logged_out_token_does_not_end_other_sessions(
        self, client: TestClient
    ) -> None:
        device_a = self._register(client)
        device_b = client.post(
            "/api/auth/login",
            json=CREDENTIALS,
        ).json()
        client.post(
            "/api/auth/logout",
            json={
                "refresh_token": device_a["refresh_token"],
            },
        )

        retry = self._refresh(client, device_a["refresh_token"])
        still_works = self._refresh(client, device_b["refresh_token"])

        assert retry.status_code == 401
        assert still_works.status_code == 200
