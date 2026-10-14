from dataclasses import dataclass

from fastapi.testclient import TestClient
from httpx2 import Response

from tests import routes
from tests.fixtures.cookies import cookie_session_headers, get_refresh_cookie
from tests.fixtures.factory import DEFAULT_ACCOUNT_EMAIL, DEFAULT_ACCOUNT_PASSWORD

CREDENTIALS = {
    "email": DEFAULT_ACCOUNT_EMAIL,
    "password": DEFAULT_ACCOUNT_PASSWORD,
}


@dataclass(frozen=True)
class BrowserSession:
    """What the browser holds: the access token in memory, the refresh
    token in its cookie store."""

    access_token: str
    refresh_token: str

    @classmethod
    def from_response(cls, response: Response) -> BrowserSession:
        return cls(
            access_token=response.json()["access_token"],
            refresh_token=get_refresh_cookie(response).value,
        )


class TestAuthSessionFlow:
    def _register(self, client: TestClient) -> BrowserSession:
        response: Response = client.post(
            routes.REGISTER,
            json=CREDENTIALS,
        )
        assert response.status_code == 201
        return BrowserSession.from_response(response)

    def _login(self, client: TestClient) -> BrowserSession:
        response: Response = client.post(routes.LOGIN, json=CREDENTIALS)
        assert response.status_code == 200
        return BrowserSession.from_response(response)

    def _refresh(self, client: TestClient, refresh_token: str) -> Response:
        return client.post(
            routes.REFRESH,
            headers=cookie_session_headers(refresh_token),
        )

    def _logout(self, client: TestClient, refresh_token: str) -> Response:
        return client.post(
            routes.LOGOUT,
            headers=cookie_session_headers(refresh_token),
        )

    def test_access_token_from_register_authenticates_me(
        self, client: TestClient
    ) -> None:
        session = self._register(client)

        response: Response = client.get(
            routes.ACCOUNTS_ME,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )

        assert response.status_code == 200
        assert response.json()["email"] == DEFAULT_ACCOUNT_EMAIL

    def test_refresh_token_is_refused_as_an_access_token(
        self, client: TestClient
    ) -> None:
        session = self._register(client)

        response: Response = client.get(
            routes.ACCOUNTS_ME,
            headers={"Authorization": f"Bearer {session.refresh_token}"},
        )

        assert response.status_code == 401

    def test_refresh_rotates_both_tokens(self, client: TestClient) -> None:
        initial_session = self._register(client)

        response = self._refresh(client, initial_session.refresh_token)

        assert response.status_code == 200
        refreshed_session = BrowserSession.from_response(response)
        assert refreshed_session.refresh_token != initial_session.refresh_token
        assert refreshed_session.access_token != initial_session.access_token

    def test_refreshed_access_token_authenticates_me(self, client: TestClient) -> None:
        initial_session = self._register(client)
        refreshed_session = BrowserSession.from_response(
            self._refresh(client, initial_session.refresh_token)
        )

        response: Response = client.get(
            routes.ACCOUNTS_ME,
            headers={"Authorization": f"Bearer {refreshed_session.access_token}"},
        )

        assert response.status_code == 200

    def test_refresh_without_the_csrf_header_does_not_rotate(
        self, client: TestClient
    ) -> None:
        session = self._register(client)

        refused = client.post(
            routes.REFRESH,
            headers=cookie_session_headers(session.refresh_token, csrf=False),
        )

        assert refused.status_code == 403
        # The token was not consumed: it still works with the header.
        assert self._refresh(client, session.refresh_token).status_code == 200

    def test_reusing_a_rotated_token_revokes_the_whole_family(
        self, client: TestClient
    ) -> None:
        initial_session = self._register(client)
        refreshed_session = BrowserSession.from_response(
            self._refresh(client, initial_session.refresh_token)
        )

        reused_token_response = self._refresh(client, initial_session.refresh_token)
        newest_token_response = self._refresh(client, refreshed_session.refresh_token)

        assert reused_token_response.status_code == 401
        # The newest token was revoked too.
        assert newest_token_response.status_code == 401

    def test_logout_revokes_the_refresh_token(self, client: TestClient) -> None:
        session = self._register(client)

        logout = self._logout(client, session.refresh_token)

        assert logout.status_code == 204
        assert get_refresh_cookie(logout)["max-age"] == "0"
        assert self._refresh(client, session.refresh_token).status_code == 401

    def test_logout_without_the_csrf_header_keeps_the_session(
        self, client: TestClient
    ) -> None:
        session = self._register(client)

        refused = client.post(
            routes.LOGOUT,
            headers=cookie_session_headers(session.refresh_token, csrf=False),
        )

        assert refused.status_code == 403
        assert self._refresh(client, session.refresh_token).status_code == 200

    def test_logout_only_ends_that_session(self, client: TestClient) -> None:
        initial_session = self._register(client)
        other_session = self._login(client)

        self._logout(client, initial_session.refresh_token)

        assert self._refresh(client, other_session.refresh_token).status_code == 200

    def test_retrying_a_logged_out_token_does_not_end_other_sessions(
        self, client: TestClient
    ) -> None:
        device_a = self._register(client)
        device_b = self._login(client)
        self._logout(client, device_a.refresh_token)

        retry = self._refresh(client, device_a.refresh_token)
        still_works = self._refresh(client, device_b.refresh_token)

        assert retry.status_code == 401
        assert still_works.status_code == 200
