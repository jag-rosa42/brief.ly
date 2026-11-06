"""Fixtures for the client credentials flow (POST /internal/v1/oauth/token)."""

from pathlib import Path

import pytest

from src.application.port.token.types import CreatedServiceToken
from src.application.use_cases.oauth.create_service_token import CreateServiceToken
from src.domain.entities.service_client import ServiceClient
from src.infrastructure.oauth.service_clients import InMemoryServiceClientRegistry

CONTENT_MANAGEMENT: str = "transcendence:content-management"
TEST_CLIENT_ID: str = "test-client"
TEST_CLIENT_SECRET: str = "test-client-secret"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
@pytest.fixture
def service_client() -> ServiceClient:
    return ServiceClient(
        client_id=TEST_CLIENT_ID,
        allowed_scopes={CONTENT_MANAGEMENT: frozenset({"topics:read", "articles:read"})},
    )


@pytest.fixture
def service_client_registry(
    service_client: ServiceClient,
) -> InMemoryServiceClientRegistry:
    return InMemoryServiceClientRegistry(clients=(service_client,))


# ---------------------------------------------------------------------------
# Client Secret Verifier
# ---------------------------------------------------------------------------
class FakeClientSecretVerifier:
    """Accepts exactly the secrets it was given, and records every call."""

    def __init__(self, secrets: dict[str, str]) -> None:
        self._secrets: dict[str, str] = secrets
        self.calls: list[str] = []

    def verify(self, client_id: str, client_secret: str) -> bool:
        self.calls.append(client_id)
        return self._secrets.get(client_id) == client_secret


@pytest.fixture
def client_secret_verifier() -> FakeClientSecretVerifier:
    return FakeClientSecretVerifier({TEST_CLIENT_ID: TEST_CLIENT_SECRET})


# ---------------------------------------------------------------------------
# Service Token Creator
# ---------------------------------------------------------------------------
class FakeServiceTokenCreator:
    """Returns a readable fake token and records what it was asked for."""

    def __init__(self) -> None:
        self.created: list[tuple[str, str, frozenset[str]]] = []

    def create_service_token(
        self,
        client_id: str,
        audience: str,
        scopes: frozenset[str],
    ) -> CreatedServiceToken:
        self.created.append((client_id, audience, scopes))
        return CreatedServiceToken(
            token=f"fake-service-token-{len(self.created)}",
            expires_in=300,
        )


@pytest.fixture
def service_token_creator() -> FakeServiceTokenCreator:
    return FakeServiceTokenCreator()


# ---------------------------------------------------------------------------
# Use case
# ---------------------------------------------------------------------------
@pytest.fixture
def create_service_token(
    service_client_registry: InMemoryServiceClientRegistry,
    client_secret_verifier: FakeClientSecretVerifier,
    service_token_creator: FakeServiceTokenCreator,
) -> CreateServiceToken:
    return CreateServiceToken(
        service_client_registry,
        client_secret_verifier,
        service_token_creator,
    )


# ---------------------------------------------------------------------------
# Secret files
# ---------------------------------------------------------------------------
@pytest.fixture
def client_secrets_dir(tmp_path: Path) -> Path:
    """A secrets folder holding the test client's secret file."""
    secret_file: Path = tmp_path / f"{TEST_CLIENT_ID.replace('-', '_')}_client_secret"
    secret_file.write_text(TEST_CLIENT_SECRET)
    return tmp_path
