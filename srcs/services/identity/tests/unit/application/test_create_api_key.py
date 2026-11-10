from datetime import timedelta
from uuid import uuid4

import pytest

from src.application.use_cases.api_keys.create_api_key import CreateApiKey, CreatedApiKey
from src.domain.entities.account import Account
from src.domain.entities.api_key import (
    API_KEY_LIFETIME,
    MAX_ACTIVE_API_KEYS_PER_ACCOUNT,
    ApiKeyScope,
)
from src.domain.exception import ApiKeyLimitReachedError, InvalidTokenError
from tests.fixtures.accounts import FakeAccountRepository
from tests.fixtures.api_keys import FakeApiKeyRepository
from tests.fixtures.factory import build_api_key
from tests.fixtures.security import FakeTokenHasher
from tests.fixtures.unit_of_work import FakeUnitOfWork

READ_WRITE = frozenset({ApiKeyScope.READ, ApiKeyScope.WRITE})


@pytest.fixture
def owner(account: Account, account_repository: FakeAccountRepository) -> Account:
    account_repository.save(account)
    return account


class TestCreateApiKey:
    def test_stores_the_key_and_commits(
        self,
        create_api_key: CreateApiKey,
        api_key_repository: FakeApiKeyRepository,
        uow: FakeUnitOfWork,
        owner: Account,
    ) -> None:
        created: CreatedApiKey = create_api_key.execute(owner.id, "my script", READ_WRITE)

        stored = api_key_repository.get(created.api_key.id)
        assert stored.account_id == owner.id
        assert stored.name == "my script"
        assert stored.scopes == READ_WRITE
        assert uow.commit_count == 1

    def test_returns_the_full_key_but_stores_only_its_hash(
        self,
        create_api_key: CreateApiKey,
        api_key_repository: FakeApiKeyRepository,
        token_hasher: FakeTokenHasher,
        owner: Account,
    ) -> None:
        created: CreatedApiKey = create_api_key.execute(owner.id, "my script", READ_WRITE)

        stored = api_key_repository.get(created.api_key.id)
        assert created.key.startswith("tr_")
        assert created.key not in (stored.key_hash, stored.prefix)
        assert created.key.startswith(stored.prefix)
        # Hashed with the TokenHasher, like refresh tokens: verify will hash
        # the key it receives the same way to find it.
        assert stored.key_hash == token_hasher.hash(created.key)

    def test_the_key_lives_48_hours(
        self,
        create_api_key: CreateApiKey,
        owner: Account,
    ) -> None:
        created: CreatedApiKey = create_api_key.execute(owner.id, "my script", READ_WRITE)

        lifetime: timedelta = created.api_key.expires_at - created.api_key.created_at
        assert lifetime == API_KEY_LIFETIME == timedelta(hours=48)

    def test_locks_the_account_before_counting(
        self,
        create_api_key: CreateApiKey,
        account_repository: FakeAccountRepository,
        owner: Account,
    ) -> None:
        create_api_key.execute(owner.id, "my script", READ_WRITE)

        assert account_repository.locked_ids == [owner.id]

    def test_refuses_a_sixth_active_key(
        self,
        create_api_key: CreateApiKey,
        api_key_repository: FakeApiKeyRepository,
        uow: FakeUnitOfWork,
        owner: Account,
    ) -> None:
        for _ in range(MAX_ACTIVE_API_KEYS_PER_ACCOUNT):
            create_api_key.execute(owner.id, "my script", READ_WRITE)

        with pytest.raises(ApiKeyLimitReachedError):
            create_api_key.execute(owner.id, "one too many", READ_WRITE)

        assert api_key_repository.count() == MAX_ACTIVE_API_KEYS_PER_ACCOUNT
        assert uow.commit_count == MAX_ACTIVE_API_KEYS_PER_ACCOUNT

    def test_revoked_and_expired_keys_do_not_count(
        self,
        create_api_key: CreateApiKey,
        api_key_repository: FakeApiKeyRepository,
        owner: Account,
    ) -> None:
        old = build_api_key(account_id=owner.id)
        api_key_repository.add(
            build_api_key(account_id=owner.id, revoked_at=old.created_at)
        )
        api_key_repository.add(
            build_api_key(
                account_id=owner.id,
                created_at=old.created_at - API_KEY_LIFETIME * 2,
            )
        )
        for _ in range(MAX_ACTIVE_API_KEYS_PER_ACCOUNT):
            create_api_key.execute(owner.id, "my script", READ_WRITE)

        assert api_key_repository.count() == MAX_ACTIVE_API_KEYS_PER_ACCOUNT + 2

    def test_the_limit_is_per_account(
        self,
        create_api_key: CreateApiKey,
        api_key_repository: FakeApiKeyRepository,
        account_repository: FakeAccountRepository,
        owner: Account,
    ) -> None:
        for _ in range(MAX_ACTIVE_API_KEYS_PER_ACCOUNT):
            api_key_repository.add(build_api_key(account_id=uuid4()))

        create_api_key.execute(owner.id, "my script", READ_WRITE)

        assert api_key_repository.count() == MAX_ACTIVE_API_KEYS_PER_ACCOUNT + 1

    def test_refuses_an_account_that_no_longer_exists(
        self,
        create_api_key: CreateApiKey,
        api_key_repository: FakeApiKeyRepository,
        uow: FakeUnitOfWork,
    ) -> None:
        with pytest.raises(InvalidTokenError):
            create_api_key.execute(uuid4(), "my script", READ_WRITE)

        assert api_key_repository.count() == 0
        assert uow.committed is False
