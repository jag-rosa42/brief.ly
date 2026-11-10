"""
Concurrency tests for the active API key limit.

Like test_refresh_token_concurrency.py, these tests open several independent
connections on the real PostgreSQL test database: data is really committed
and deleted at the end of each test.
"""

import threading
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import Engine, delete, func, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from src.application.port.password_hasher import PasswordHasher
from src.application.use_cases.api_keys.create_api_key import CreateApiKey
from src.domain.entities.account import Account
from src.domain.entities.api_key import MAX_ACTIVE_API_KEYS_PER_ACCOUNT, ApiKeyScope
from src.domain.exception import ApiKeyLimitReachedError
from src.infrastructure.database.models.account import Account as AccountModel
from src.infrastructure.database.models.api_key import ApiKey as ApiKeyModel
from src.infrastructure.database.repositories.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)
from src.infrastructure.database.repositories.sqlalchemy_api_key_repository import (
    SqlAlchemyApiKeyRepository,
)
from src.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.security.api_key_generator import SecretsApiKeyGenerator
from src.infrastructure.security.token_hasher import Sha256TokenHasher
from tests.fixtures.factory import DEFAULT_ACCOUNT_PASSWORD, build_account

READ = frozenset({ApiKeyScope.READ})


@pytest.fixture
def committed_account(
    engine: Engine,
    password_hasher: PasswordHasher,
) -> Generator[Account]:
    account: Account = build_account(
        email=f"api-key-concurrency-{uuid4()}@example.com",
        password_hash=password_hasher.hash(DEFAULT_ACCOUNT_PASSWORD),
    )
    with Session(engine) as session:
        SqlAlchemyAccountRepository(session).save(account)
        session.commit()
    try:
        yield account
    finally:
        # ON DELETE CASCADE removes the account's API keys too.
        with Session(engine) as session:
            session.execute(delete(AccountModel).where(AccountModel.id == account.id))
            session.commit()


def _build_create_api_key(session: Session) -> CreateApiKey:
    return CreateApiKey(
        SqlAlchemyUnitOfWork(session),
        SqlAlchemyAccountRepository(session),
        SqlAlchemyApiKeyRepository(session),
        SecretsApiKeyGenerator(),
        Sha256TokenHasher(),
    )


class TestAccountRowLock:
    def test_for_update_blocks_a_second_locker(
        self,
        engine: Engine,
        committed_account: Account,
    ) -> None:
        with Session(engine) as holder, Session(engine) as waiter:
            SqlAlchemyAccountRepository(holder).find_by_id_for_update(
                committed_account.id
            )

            # A second FOR UPDATE must wait: give up after 200ms instead of
            # hanging, and check that it actually had to wait.
            waiter.execute(text("SET LOCAL lock_timeout = '200ms'"))
            with pytest.raises(OperationalError):
                SqlAlchemyAccountRepository(waiter).find_by_id_for_update(
                    committed_account.id
                )
            waiter.rollback()
            holder.rollback()


class TestConcurrentCreation:
    def test_concurrent_creations_never_exceed_the_limit(
        self,
        engine: Engine,
        committed_account: Account,
    ) -> None:
        # One key short of the limit: exactly one of the concurrent requests
        # may create the last key.
        with Session(engine) as session:
            for _ in range(MAX_ACTIVE_API_KEYS_PER_ACCOUNT - 1):
                _build_create_api_key(session).execute(
                    committed_account.id, "setup", READ
                )

        requests: int = 4
        start = threading.Barrier(requests)

        def create() -> str:
            with Session(engine) as session:
                start.wait()  # all threads start together
                try:
                    _build_create_api_key(session).execute(
                        committed_account.id, "race", READ
                    )
                except ApiKeyLimitReachedError:
                    return "refused"
                return "created"

        with ThreadPoolExecutor(max_workers=requests) as pool:
            results: list[str] = list(pool.map(lambda _: create(), range(requests)))

        assert sorted(results) == ["created"] + ["refused"] * (requests - 1)
        with Session(engine) as session:
            stored: int = session.execute(
                select(func.count())
                .select_from(ApiKeyModel)
                .where(ApiKeyModel.account_id == committed_account.id)
            ).scalar_one()
        assert stored == MAX_ACTIVE_API_KEYS_PER_ACCOUNT
