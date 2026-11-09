"""
Concurrency tests for refresh-token rotation.

These tests open several independent connections on the real PostgreSQL
test database, so they cannot use the per-test rollback of ``db_session``:
data is really committed and deleted at the end of each test.
"""

import threading
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import Engine, delete, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from src.application.port.password_hasher import PasswordHasher
from src.application.use_cases.session.account_session import AccountSession
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.application.use_cases.session.refresh_account_session import (
    RefreshAccountSession,
)
from src.application.use_cases.session.refresh_token_validator import (
    RefreshTokenValidator,
)
from src.domain.entities.account import Account
from src.domain.exception import DomainError, TokenRevokedError
from src.infrastructure.database.models.account import Account as AccountModel
from src.infrastructure.database.models.refresh_token import (
    RefreshToken as RefreshTokenModel,
)
from src.infrastructure.database.repositories.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)
from src.infrastructure.database.repositories.sqlalchemy_refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from src.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.security.token.token_service import JWTTokenService
from src.infrastructure.security.token_hasher import Sha256TokenHasher
from tests.fixtures.factory import DEFAULT_ACCOUNT_PASSWORD, build_account


@pytest.fixture
def committed_account(
    engine: Engine,
    password_hasher: PasswordHasher,
) -> Generator[Account]:
    account: Account = build_account(
        email=f"concurrency-{uuid4()}@example.com",
        password_hash=password_hasher.hash(DEFAULT_ACCOUNT_PASSWORD),
    )
    with Session(engine) as session:
        SqlAlchemyAccountRepository(session).save(account)
        session.commit()
    try:
        yield account
    finally:
        # ON DELETE CASCADE removes the account's refresh tokens too.
        with Session(engine) as session:
            session.execute(delete(AccountModel).where(AccountModel.id == account.id))
            session.commit()


@pytest.fixture
def committed_session(engine: Engine, committed_account: Account) -> AccountSession:
    """A real JWT refresh token, committed for the account."""
    with Session(engine) as session:
        account_session = CreateAccountSession(
            SqlAlchemyRefreshTokenRepository(session),
            JWTTokenService(),
            Sha256TokenHasher(),
        ).execute(committed_account.id)
        session.commit()
    return account_session


def _build_refresh_account_session(session: Session) -> RefreshAccountSession:
    token_service = JWTTokenService()
    token_hasher = Sha256TokenHasher()
    repository = SqlAlchemyRefreshTokenRepository(session)
    return RefreshAccountSession(
        SqlAlchemyUnitOfWork(session),
        RefreshTokenValidator(repository, token_service, token_hasher),
        repository,
        CreateAccountSession(repository, token_service, token_hasher),
    )


class TestRefreshTokenRowLock:
    def test_for_update_blocks_a_second_locker_but_not_a_plain_read(
        self,
        engine: Engine,
        committed_session: AccountSession,
    ) -> None:
        token_id = committed_session.refresh_token_id

        with Session(engine) as holder, Session(engine) as waiter:
            # The holder takes the lock and keeps its transaction open.
            SqlAlchemyRefreshTokenRepository(holder).find_by_id_for_update(token_id)

            # A plain SELECT is not blocked (PostgreSQL MVCC).
            assert SqlAlchemyRefreshTokenRepository(waiter).find_by_id(token_id)

            # A second FOR UPDATE must wait. Give up after 200ms instead
            # of hanging, and check that it actually had to wait.
            waiter.execute(text("SET LOCAL lock_timeout = '200ms'"))
            with pytest.raises(OperationalError):
                SqlAlchemyRefreshTokenRepository(waiter).find_by_id_for_update(token_id)
            waiter.rollback()

            # Ending the holder's transaction releases the lock.
            holder.rollback()
            assert SqlAlchemyRefreshTokenRepository(waiter).find_by_id_for_update(
                token_id
            )
            waiter.rollback()


class TestConcurrentRefresh:
    def test_the_same_token_refreshed_twice_concurrently_is_rotated_once(
        self,
        engine: Engine,
        committed_account: Account,
        committed_session: AccountSession,
    ) -> None:
        # timeout: never hang the test suite if one thread fails early.
        start_together = threading.Barrier(2, timeout=5)

        def refresh() -> AccountSession | DomainError:
            with Session(engine) as session:
                use_case = _build_refresh_account_session(session)
                start_together.wait()
                try:
                    return use_case.execute(committed_session.refresh_token)
                except DomainError as exc:
                    return exc

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: refresh(), range(2)))

        sessions = [r for r in results if isinstance(r, AccountSession)]
        errors = [r for r in results if isinstance(r, DomainError)]

        # Without the lock, both requests usually succeed here.
        assert len(sessions) == 1
        assert len(errors) == 1
        assert isinstance(errors[0], TokenRevokedError)

        with Session(engine) as session:
            active = session.scalars(
                select(RefreshTokenModel)
                .where(RefreshTokenModel.account_id == committed_account.id)
                .where(RefreshTokenModel.revoked_at.is_(None))
            ).all()
        assert active == []
