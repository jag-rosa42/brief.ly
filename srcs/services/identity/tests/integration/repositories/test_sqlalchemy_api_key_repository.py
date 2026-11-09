from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.entities.account import Account
from src.domain.entities.api_key import API_KEY_LIFETIME, ApiKey, ApiKeyScope
from src.infrastructure.database.models.account import Account as AccountModel
from src.infrastructure.database.models.api_key import ApiKey as ApiKeyModel
from src.infrastructure.database.repositories.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)
from src.infrastructure.database.repositories.sqlalchemy_api_key_repository import (
    SqlAlchemyApiKeyRepository,
)
from tests.fixtures.factory import build_api_key


@pytest.fixture
def persisted_account(db_session: Session, account: Account) -> Account:
    SqlAlchemyAccountRepository(db_session).save(account)
    db_session.flush()
    return account


@pytest.fixture
def repository(db_session: Session) -> SqlAlchemyApiKeyRepository:
    return SqlAlchemyApiKeyRepository(db_session)


class TestSqlAlchemyApiKeyRepository:
    def test_add_makes_the_key_findable_by_id_and_by_hash(
        self,
        repository: SqlAlchemyApiKeyRepository,
        db_session: Session,
        persisted_account: Account,
    ) -> None:
        api_key: ApiKey = build_api_key(
            account_id=persisted_account.id,
            scopes=frozenset({ApiKeyScope.READ, ApiKeyScope.WRITE}),
        )
        repository.add(api_key)
        db_session.flush()
        db_session.expire_all()

        assert repository.find_by_id(api_key.id) == api_key
        assert repository.find_by_hash(api_key.key_hash) == api_key

    def test_find_returns_none_for_unknown_keys(
        self, repository: SqlAlchemyApiKeyRepository
    ) -> None:
        assert repository.find_by_id(uuid4()) is None
        assert repository.find_by_hash("unknown-hash") is None

    def test_update_persists_the_revocation(
        self,
        repository: SqlAlchemyApiKeyRepository,
        db_session: Session,
        persisted_account: Account,
    ) -> None:
        api_key: ApiKey = build_api_key(account_id=persisted_account.id)
        repository.add(api_key)
        db_session.flush()

        api_key.revoke(datetime.now(UTC))
        assert repository.update(api_key) is True
        db_session.expire_all()

        stored = repository.find_by_id(api_key.id)
        assert stored is not None
        assert stored.revoked_at == api_key.revoked_at

    def test_update_never_revokes_twice(
        self,
        repository: SqlAlchemyApiKeyRepository,
        db_session: Session,
        persisted_account: Account,
    ) -> None:
        first = datetime.now(UTC)
        api_key: ApiKey = build_api_key(account_id=persisted_account.id)
        repository.add(api_key)
        db_session.flush()
        api_key.revoke(first)
        repository.update(api_key)

        api_key.revoked_at = first + timedelta(minutes=1)
        assert repository.update(api_key) is False
        db_session.expire_all()

        stored = repository.find_by_id(api_key.id)
        assert stored is not None
        assert stored.revoked_at == first

    def test_active_queries_skip_revoked_expired_and_other_accounts(
        self,
        repository: SqlAlchemyApiKeyRepository,
        db_session: Session,
        persisted_account: Account,
    ) -> None:
        now = datetime.now(UTC)
        account_id = persisted_account.id
        older = build_api_key(account_id=account_id, created_at=now - timedelta(hours=2))
        newer = build_api_key(account_id=account_id, created_at=now - timedelta(hours=1))
        revoked = build_api_key(account_id=persisted_account.id, revoked_at=now)
        expired = build_api_key(
            account_id=persisted_account.id, created_at=now - API_KEY_LIFETIME * 2
        )
        for api_key in (older, newer, revoked, expired):
            repository.add(api_key)
        db_session.flush()

        active = repository.list_active_for_account(persisted_account.id, now)

        assert [api_key.id for api_key in active] == [newer.id, older.id]
        assert repository.count_active_for_account(persisted_account.id, now) == 2
        assert repository.count_active_for_account(uuid4(), now) == 0

    def test_keys_are_deleted_with_their_account(
        self,
        repository: SqlAlchemyApiKeyRepository,
        db_session: Session,
        persisted_account: Account,
    ) -> None:
        api_key: ApiKey = build_api_key(account_id=persisted_account.id)
        repository.add(api_key)
        db_session.flush()

        db_session.execute(
            delete(AccountModel).where(AccountModel.id == persisted_account.id)
        )
        db_session.flush()

        assert repository.find_by_id(api_key.id) is None


class TestScopesCheckConstraint:
    """ck_api_keys_scopes: the last line of defence, below the domain.

    The domain can't even build these values (ApiKeyScope), so the rows are
    written with the SQLAlchemy model directly, like a buggy query would.
    """

    @pytest.mark.parametrize(
        "scopes",
        [["admin"], ["read", "admin"], ["READ"], []],
    )
    def test_refuses_scopes_other_than_read_and_write(
        self,
        db_session: Session,
        persisted_account: Account,
        scopes: list[str],
    ) -> None:
        now = datetime.now(UTC)
        db_session.add(
            ApiKeyModel(
                id=uuid4(),
                account_id=persisted_account.id,
                name="bad scopes",
                prefix="tr_test",
                key_hash=f"hash-{uuid4()}",
                scopes=scopes,
                created_at=now,
                expires_at=now + API_KEY_LIFETIME,
            )
        )

        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()

    @pytest.mark.parametrize("scopes", [["read"], ["write"], ["read", "write"]])
    def test_accepts_read_and_write(
        self,
        repository: SqlAlchemyApiKeyRepository,
        db_session: Session,
        persisted_account: Account,
        scopes: list[str],
    ) -> None:
        api_key: ApiKey = build_api_key(
            account_id=persisted_account.id,
            scopes=frozenset(ApiKeyScope(scope) for scope in scopes),
        )
        repository.add(api_key)
        db_session.flush()

        assert repository.find_by_id(api_key.id) == api_key


class TestFindAccountForUpdate:
    def test_returns_the_account(
        self, db_session: Session, persisted_account: Account
    ) -> None:
        found = SqlAlchemyAccountRepository(db_session).find_by_id_for_update(
            persisted_account.id
        )

        assert found is not None
        assert found.id == persisted_account.id

    def test_returns_none_for_an_unknown_account(self, db_session: Session) -> None:
        repository = SqlAlchemyAccountRepository(db_session)

        assert repository.find_by_id_for_update(uuid4()) is None
