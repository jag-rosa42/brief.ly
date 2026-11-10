"""POST /api-keys through the whole stack, without a database.

Real access tokens, checked by the real CurrentAccountDep; real use cases,
real key generator. Only the repositories and the unit of work are
in-memory fakes, so these tests don't need PostgreSQL.
"""

from collections.abc import Generator
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_errors import ErrorResponse

from src.api.dependencies.account import get_account_repository
from src.api.dependencies.api_key import get_api_key_repository
from src.api.dependencies.database import get_unit_of_work
from src.domain.entities.account import Account
from src.domain.entities.api_key import MAX_ACTIVE_API_KEYS_PER_ACCOUNT
from src.infrastructure.security.token.token_service import JWTTokenService
from src.main import app
from tests import routes
from tests.fixtures.accounts import FakeAccountRepository
from tests.fixtures.api_keys import FakeApiKeyRepository
from tests.fixtures.unit_of_work import FakeUnitOfWork

NEW_KEY: dict[str, Any] = {"name": "my script", "scopes": ["read", "write"]}


def error_code(response: Response) -> str:
    return ErrorResponse.model_validate(response.json()).error.code


@pytest.fixture
def client(
    account_repository: FakeAccountRepository,
    api_key_repository: FakeApiKeyRepository,
    uow: FakeUnitOfWork,
) -> Generator[TestClient]:
    """TestClient whose repositories are in memory (shadows the DB client)."""
    app.dependency_overrides[get_account_repository] = lambda: account_repository
    app.dependency_overrides[get_api_key_repository] = lambda: api_key_repository
    app.dependency_overrides[get_unit_of_work] = lambda: uow
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def owner(account: Account, account_repository: FakeAccountRepository) -> Account:
    account_repository.save(account)
    return account


@pytest.fixture
def auth(owner: Account, jwt_token_service: JWTTokenService) -> dict[str, str]:
    """A real access token for `owner`, as the frontend sends it."""
    return {"Authorization": f"Bearer {jwt_token_service.create_access_token(owner.id)}"}


class TestCreateApiKey:
    def test_returns_201_with_the_full_key(
        self, client: TestClient, auth: dict[str, str]
    ) -> None:
        response: Response = client.post(routes.API_KEYS, json=NEW_KEY, headers=auth)

        assert response.status_code == 201
        body: dict[str, Any] = response.json()
        assert body["name"] == "my script"
        assert body["scopes"] == ["read", "write"]
        assert body["key"].startswith("tr_")
        assert body["key"].startswith(body["prefix"])
        expires_at = datetime.fromisoformat(body["expires_at"])
        created_at = datetime.fromisoformat(body["created_at"])
        assert expires_at - created_at == timedelta(hours=48)

    def test_the_answer_is_never_cached(
        self, client: TestClient, auth: dict[str, str]
    ) -> None:
        response: Response = client.post(routes.API_KEYS, json=NEW_KEY, headers=auth)

        assert response.headers["Cache-Control"] == "no-store"

    def test_creates_the_key_for_the_token_account(
        self,
        client: TestClient,
        auth: dict[str, str],
        owner: Account,
        api_key_repository: FakeApiKeyRepository,
    ) -> None:
        response: Response = client.post(routes.API_KEYS, json=NEW_KEY, headers=auth)

        stored = api_key_repository.get(UUID(response.json()["id"]))
        assert stored.account_id == owner.id
        # Only the hash is stored, never the key.
        assert stored.key_hash != response.json()["key"]

    def test_returns_409_after_five_active_keys(
        self, client: TestClient, auth: dict[str, str]
    ) -> None:
        for _ in range(MAX_ACTIVE_API_KEYS_PER_ACCOUNT):
            created = client.post(routes.API_KEYS, json=NEW_KEY, headers=auth)
            assert created.status_code == 201

        response: Response = client.post(routes.API_KEYS, json=NEW_KEY, headers=auth)

        assert response.status_code == 409
        assert error_code(response) == "API_KEY_LIMIT_REACHED"

    @pytest.mark.parametrize(
        "body",
        [
            {"name": "", "scopes": ["read"]},
            {"name": "   ", "scopes": ["read"]},
            {"name": "x" * 51, "scopes": ["read"]},
            {"name": "my script", "scopes": []},
            {"name": "my script", "scopes": ["admin"]},
            {"name": "my script", "scopes": ["read", "read"]},
            {"name": "my script", "scopes": ["read", "write", "read"]},
            {"scopes": ["read"]},
            {"name": "my script"},
        ],
    )
    def test_returns_422_for_an_invalid_body(
        self, client: TestClient, auth: dict[str, str], body: dict[str, Any]
    ) -> None:
        response: Response = client.post(routes.API_KEYS, json=body, headers=auth)

        assert response.status_code == 422
        assert error_code(response) == "VALIDATION_ERROR"

    def test_trims_the_name(self, client: TestClient, auth: dict[str, str]) -> None:
        body: dict[str, Any] = {"name": "  my script  ", "scopes": ["read"]}

        response: Response = client.post(routes.API_KEYS, json=body, headers=auth)

        assert response.json()["name"] == "my script"

    def test_returns_401_without_a_token(self, client: TestClient) -> None:
        response: Response = client.post(routes.API_KEYS, json=NEW_KEY)

        assert response.status_code == 401
        assert error_code(response) == "INVALID_TOKEN"
