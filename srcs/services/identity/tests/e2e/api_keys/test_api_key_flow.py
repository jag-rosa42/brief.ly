"""The whole life of an API key, with the real database.

register -> create a key -> the gateway verifies it -> revoke -> refused.
"""

from typing import Any
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient
from httpx2 import Response

from src.infrastructure.security.settings import security_settings
from tests import routes


def register(client: TestClient) -> dict[str, str]:
    response: Response = client.post(
        routes.REGISTER,
        json={"email": f"john.doe-{uuid4()}@example.com", "password": "super-secret"},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


class TestApiKeyFlow:
    def test_a_key_works_until_it_is_revoked(self, client: TestClient) -> None:
        auth: dict[str, str] = register(client)

        created: Response = client.post(
            routes.API_KEYS,
            json={"name": "my script", "scopes": ["read"]},
            headers=auth,
        )
        assert created.status_code == 201
        key: str = created.json()["key"]

        verified: Response = client.get(
            routes.API_KEYS_VERIFY, headers={"X-API-Key": key}
        )
        assert verified.status_code == 200
        token: str = verified.headers["Authorization"].removeprefix("Bearer ")
        claims: dict[str, Any] = jwt.decode(
            token,
            security_settings.JWT_PUBLIC_KEY,
            algorithms=["RS256"],
            audience=security_settings.JWT_PUBLIC_API_AUDIENCE,
            issuer=security_settings.JWT_ISSUER,
        )
        assert claims["scope"] == "read"

        listed: Response = client.get(routes.API_KEYS, headers=auth)
        assert [item["id"] for item in listed.json()["items"]] == [created.json()["id"]]
        assert "key" not in listed.json()["items"][0]

        revoked: Response = client.delete(
            routes.api_key(created.json()["id"]), headers=auth
        )
        assert revoked.status_code == 204

        # Immediate: the very next verification fails.
        refused: Response = client.get(routes.API_KEYS_VERIFY, headers={"X-API-Key": key})
        assert refused.status_code == 401
        assert client.get(routes.API_KEYS, headers=auth).json() == {"items": []}

    def test_a_user_cannot_revoke_another_users_key(self, client: TestClient) -> None:
        alice: dict[str, str] = register(client)
        bob: dict[str, str] = register(client)
        created: Response = client.post(
            routes.API_KEYS, json={"name": "alice", "scopes": ["read"]}, headers=alice
        )

        response: Response = client.delete(
            routes.api_key(created.json()["id"]), headers=bob
        )

        assert response.status_code == 204
        still_valid: Response = client.get(
            routes.API_KEYS_VERIFY, headers={"X-API-Key": created.json()["key"]}
        )
        assert still_valid.status_code == 200
