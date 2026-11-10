"""Fixtures for the Public API keys (ADR-0009)."""

from dataclasses import replace
from datetime import datetime
from uuid import UUID

import pytest

from src.application.port.api_key.generator import GeneratedApiKey
from src.application.use_cases.api_keys.create_api_key import CreateApiKey
from src.application.use_cases.api_keys.list_api_keys import ListApiKeys
from src.application.use_cases.api_keys.revoke_api_key import RevokeApiKey
from src.application.use_cases.api_keys.verify_api_key import VerifyApiKey
from src.domain.entities.api_key import ApiKey, ApiKeyScope
from tests.fixtures.accounts import FakeAccountRepository
from tests.fixtures.security import FakeTokenHasher
from tests.fixtures.unit_of_work import FakeUnitOfWork


# ---------------------------------------------------------------------------
# API Key Repository
# ---------------------------------------------------------------------------
class FakeApiKeyRepository:
    """In-memory ApiKeyRepository, with the same rules as the SQL one."""

    def __init__(self) -> None:
        self._api_keys_by_id: dict[UUID, ApiKey] = {}

    def add(self, api_key: ApiKey) -> None:
        self._api_keys_by_id[api_key.id] = replace(api_key)

    def update(self, api_key: ApiKey) -> bool:
        stored: ApiKey | None = self._api_keys_by_id.get(api_key.id)
        # Same compare-and-set as the SQL version: WHERE revoked_at IS NULL.
        if stored is None or stored.is_revoked():
            return False
        stored.revoked_at = api_key.revoked_at
        return True

    def find_by_id(self, api_key_id: UUID) -> ApiKey | None:
        stored: ApiKey | None = self._api_keys_by_id.get(api_key_id)
        # A copy, like a database read: changing it changes nothing stored.
        return None if stored is None else replace(stored)

    def find_by_hash(self, key_hash: str) -> ApiKey | None:
        for stored in self._api_keys_by_id.values():
            if stored.key_hash == key_hash:
                return replace(stored)
        return None

    def count_active_for_account(self, account_id: UUID, now: datetime) -> int:
        return len(self.list_active_for_account(account_id, now))

    def list_active_for_account(self, account_id: UUID, now: datetime) -> list[ApiKey]:
        active: list[ApiKey] = [
            replace(stored)
            for stored in self._api_keys_by_id.values()
            if stored.account_id == account_id and stored.is_active(now)
        ]
        return sorted(active, key=lambda api_key: api_key.created_at, reverse=True)

    # Test helpers
    def get(self, api_key_id: UUID) -> ApiKey:
        stored: ApiKey | None = self.find_by_id(api_key_id)
        assert stored is not None, f"api_key {api_key_id} was not stored"
        return stored

    def count(self) -> int:
        return len(self._api_keys_by_id)


@pytest.fixture
def api_key_repository() -> FakeApiKeyRepository:
    return FakeApiKeyRepository()


# ---------------------------------------------------------------------------
# API Key Generator
# ---------------------------------------------------------------------------
class FakeApiKeyGenerator:
    """Predictable keys: tr_fake-1, tr_fake-2, ..."""

    def __init__(self) -> None:
        self._count: int = 0

    def generate(self) -> GeneratedApiKey:
        self._count += 1
        key: str = f"tr_fake-{self._count}"
        return GeneratedApiKey(key=key, prefix=key[:7])


@pytest.fixture
def api_key_generator() -> FakeApiKeyGenerator:
    return FakeApiKeyGenerator()


# ---------------------------------------------------------------------------
# Public API Token Creator
# ---------------------------------------------------------------------------
class FakePublicApiTokenCreator:
    """Records what it was asked to sign, and returns a readable fake token."""

    def __init__(self) -> None:
        self.calls: list[tuple[UUID, frozenset[ApiKeyScope]]] = []

    def create_public_api_token(
        self, account_id: UUID, scopes: frozenset[ApiKeyScope]
    ) -> str:
        self.calls.append((account_id, scopes))
        return f"fake-public-api-token-for-{account_id}"


@pytest.fixture
def public_api_token_creator() -> FakePublicApiTokenCreator:
    return FakePublicApiTokenCreator()


# ---------------------------------------------------------------------------
# Use cases, wired to the fakes
# ---------------------------------------------------------------------------
@pytest.fixture
def create_api_key(
    uow: FakeUnitOfWork,
    account_repository: FakeAccountRepository,
    api_key_repository: FakeApiKeyRepository,
    api_key_generator: FakeApiKeyGenerator,
    token_hasher: FakeTokenHasher,
) -> CreateApiKey:
    return CreateApiKey(
        uow,
        account_repository,
        api_key_repository,
        api_key_generator,
        token_hasher,
    )


@pytest.fixture
def list_api_keys(api_key_repository: FakeApiKeyRepository) -> ListApiKeys:
    return ListApiKeys(api_key_repository)


@pytest.fixture
def revoke_api_key(
    uow: FakeUnitOfWork,
    api_key_repository: FakeApiKeyRepository,
) -> RevokeApiKey:
    return RevokeApiKey(uow, api_key_repository)


@pytest.fixture
def verify_api_key(
    api_key_repository: FakeApiKeyRepository,
    token_hasher: FakeTokenHasher,
    public_api_token_creator: FakePublicApiTokenCreator,
) -> VerifyApiKey:
    return VerifyApiKey(
        api_key_repository,
        token_hasher,
        public_api_token_creator,
    )
