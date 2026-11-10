"""/internal/v1/api-keys/verify through the whole stack, without a database.

Called the way Traefik's ForwardAuth calls it: the original request's
headers, X-API-Key among them. Real key generator, real hasher, real JWT
signing; only the repository is an in-memory fake.
"""

from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_errors import ErrorResponse

from src.api.dependencies.api_key import get_api_key_repository
from src.application.port.api_key.generator import GeneratedApiKey
from src.domain.entities.api_key import API_KEY_LIFETIME, ApiKeyScope
from src.infrastructure.security.api_key_generator import SecretsApiKeyGenerator
from src.infrastructure.security.settings import security_settings
from src.infrastructure.security.token_hasher import Sha256TokenHasher
from src.main import app
from tests import routes
from tests.fixtures.api_keys import FakeApiKeyRepository
from tests.fixtures.factory import build_api_key

PUBLIC_API: str = "transcendence:public-api"
API_KEY_CHALLENGE: str = 'ApiKey header="X-API-Key"'


def error_code(response: Response) -> str:
    return ErrorResponse.model_validate(response.json()).error.code


def assert_invalid_api_key(response: Response) -> None:
    """401 INVALID_API_KEY, naming the header to send (RFC 9110 §15.5.2)."""
    assert response.status_code == 401
    assert error_code(response) == "INVALID_API_KEY"
    assert response.headers["WWW-Authenticate"] == API_KEY_CHALLENGE


def bearer_claims(response: Response) -> dict[str, Any]:
    scheme, _, token = response.headers["Authorization"].partition(" ")
    assert scheme == "Bearer"
    return jwt.decode(
        token,
        security_settings.JWT_PUBLIC_KEY,
        algorithms=["RS256"],
        audience=PUBLIC_API,
        issuer=security_settings.JWT_ISSUER,
    )


@pytest.fixture
def client(api_key_repository: FakeApiKeyRepository) -> Generator[TestClient]:
    """TestClient whose key repository is in memory (shadows the DB client)."""
    app.dependency_overrides[get_api_key_repository] = lambda: api_key_repository
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def generated() -> GeneratedApiKey:
    return SecretsApiKeyGenerator().generate()


@pytest.fixture
def key_hash(generated: GeneratedApiKey) -> str:
    """The hash CreateApiKey would have stored for `generated`."""
    return Sha256TokenHasher().hash(generated.key)


class TestVerifyApiKeyRouter:
    @pytest.mark.parametrize("method", ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"])
    def test_returns_200_with_a_public_api_token_for_any_method(
        self,
        client: TestClient,
        api_key_repository: FakeApiKeyRepository,
        generated: GeneratedApiKey,
        key_hash: str,
        method: str,
    ) -> None:
        api_key = build_api_key(
            key_hash=key_hash,
            scopes=frozenset({ApiKeyScope.READ, ApiKeyScope.WRITE}),
        )
        api_key_repository.add(api_key)

        response: Response = client.request(
            method, routes.API_KEYS_VERIFY, headers={"X-API-Key": generated.key}
        )

        assert response.status_code == 200
        assert response.content == b""
        assert response.headers["Cache-Control"] == "no-store"
        claims: dict[str, Any] = bearer_claims(response)
        assert claims["sub"] == str(api_key.account_id)
        assert claims["type"] == "access"
        assert claims["scope"] == "read write"

    def test_the_token_carries_only_the_key_scopes(
        self,
        client: TestClient,
        api_key_repository: FakeApiKeyRepository,
        generated: GeneratedApiKey,
        key_hash: str,
    ) -> None:
        api_key_repository.add(
            build_api_key(key_hash=key_hash, scopes=frozenset({ApiKeyScope.READ}))
        )

        response: Response = client.get(
            routes.API_KEYS_VERIFY, headers={"X-API-Key": generated.key}
        )

        assert bearer_claims(response)["scope"] == "read"

    def test_returns_401_without_a_key(self, client: TestClient) -> None:
        response: Response = client.get(routes.API_KEYS_VERIFY)

        assert_invalid_api_key(response)
        assert "Authorization" not in response.headers

    def test_returns_401_for_an_unknown_key(
        self, client: TestClient, generated: GeneratedApiKey
    ) -> None:
        response: Response = client.get(
            routes.API_KEYS_VERIFY, headers={"X-API-Key": generated.key}
        )

        assert_invalid_api_key(response)

    def test_returns_401_for_a_revoked_key(
        self,
        client: TestClient,
        api_key_repository: FakeApiKeyRepository,
        generated: GeneratedApiKey,
        key_hash: str,
    ) -> None:
        api_key_repository.add(
            build_api_key(key_hash=key_hash, revoked_at=datetime.now(UTC))
        )

        response: Response = client.get(
            routes.API_KEYS_VERIFY, headers={"X-API-Key": generated.key}
        )

        assert_invalid_api_key(response)

    def test_returns_401_for_an_expired_key(
        self,
        client: TestClient,
        api_key_repository: FakeApiKeyRepository,
        generated: GeneratedApiKey,
        key_hash: str,
    ) -> None:
        api_key_repository.add(
            build_api_key(
                key_hash=key_hash,
                created_at=datetime.now(UTC) - API_KEY_LIFETIME * 2,
            )
        )

        response: Response = client.get(
            routes.API_KEYS_VERIFY, headers={"X-API-Key": generated.key}
        )

        assert_invalid_api_key(response)

    def test_ignores_a_bearer_token_sent_by_the_program(
        self, client: TestClient, generated: GeneratedApiKey
    ) -> None:
        # Only X-API-Key counts: a token the program forged or stole doesn't
        # turn an unknown key into a valid one.
        response: Response = client.get(
            routes.API_KEYS_VERIFY,
            headers={"X-API-Key": generated.key, "Authorization": "Bearer anything"},
        )

        assert_invalid_api_key(response)
