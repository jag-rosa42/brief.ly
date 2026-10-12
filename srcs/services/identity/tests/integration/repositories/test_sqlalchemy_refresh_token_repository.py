from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.application.port.password_hasher import PasswordHasher
from src.domain.entities.account import Account
from src.domain.entities.refresh_token import RefreshToken
from src.infrastructure.database.models.account import Account as AccountModel
from src.infrastructure.database.repositories.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)
from src.infrastructure.database.repositories.sqlalchemy_refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from tests.fixtures.factory import build_account, build_refresh_token


@pytest.fixture
def persisted_account(db_session: Session, account: Account) -> Account:
    SqlAlchemyAccountRepository(db_session).save(account)
    db_session.flush()
    return account


@pytest.fixture
def repository(db_session: Session) -> SqlAlchemyRefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(db_session)


class TestSqlAlchemyRefreshTokenRepository:
    def test_add_makes_the_token_findable_by_id(
        self,
        repository: SqlAlchemyRefreshTokenRepository,
        db_session: Session,
        persisted_account: Account,
    ) -> None:
        token = build_refresh_token(account_id=persisted_account.id)
        repository.add(token)
        db_session.flush()

        result: RefreshToken | None = repository.find_by_id(token.id)
        assert result == token

    def test_find_by_id_returns_none_for_an_unknown_id(
        self,
        repository: SqlAlchemyRefreshTokenRepository,
    ) -> None:
        result: RefreshToken | None = repository.find_by_id(uuid4())

        assert result is None

    def test_update_persists_the_revocation_and_its_replacement(
        self,
        repository: SqlAlchemyRefreshTokenRepository,
        db_session: Session,
        persisted_account: Account,
    ) -> None:
        old_token = build_refresh_token(account_id=persisted_account.id)
        new_token = build_refresh_token(account_id=persisted_account.id)
        repository.add(old_token)
        repository.add(new_token)
        db_session.flush()  # `new` must exist before `old` can point to it

        old_token.revoke(datetime.now(UTC), replaced_by=new_token.id)
        repository.update(old_token)
        db_session.flush()
        db_session.expire_all()

        result = repository.find_by_id(old_token.id)
        assert result is not None
        assert result.revoked_at == old_token.revoked_at
        assert result.replaced_by == new_token.id

    def test_update_returns_false_for_an_unknown_token(
        self,
        repository: SqlAlchemyRefreshTokenRepository,
        persisted_account: Account,
    ) -> None:
        unknown = build_refresh_token(account_id=persisted_account.id)
        unknown.revoke(datetime.now(UTC))

        assert repository.update(unknown) is False

    def test_replacement_must_reference_an_existing_token(
        self,
        repository: SqlAlchemyRefreshTokenRepository,
        db_session: Session,
        persisted_account: Account,
    ) -> None:
        token = build_refresh_token(account_id=persisted_account.id)
        repository.add(token)
        db_session.flush()

        token.revoke(datetime.now(UTC), replaced_by=uuid4())
        # update() executes the UPDATE immediately (it needs RETURNING to know
        # whether the compare-and-set matched), so the foreign key on
        # replaced_by_id is checked here, not at the next flush.
        with pytest.raises(IntegrityError):
            repository.update(token)
        db_session.rollback()

    def test_revoke_all_for_account_only_revokes_its_active_tokens(
        self,
        repository: SqlAlchemyRefreshTokenRepository,
        db_session: Session,
        persisted_account: Account,
        password_hasher: PasswordHasher,
    ) -> None:
        other_account = build_account(
            email="other@example.com",
            password_hash=password_hasher.hash("secure-password"),
        )
        SqlAlchemyAccountRepository(db_session).save(other_account)
        db_session.flush()

        earlier = datetime.now(UTC) - timedelta(days=1)
        active = build_refresh_token(account_id=persisted_account.id)
        already_revoked = build_refresh_token(
            account_id=persisted_account.id, revoked_at=earlier
        )
        other = build_refresh_token(account_id=other_account.id)
        for token in (active, already_revoked, other):
            repository.add(token)
        db_session.flush()

        now = datetime.now(UTC)
        repository.revoke_all_for_account(persisted_account.id, now)
        db_session.expire_all()

        result_active = repository.find_by_id(active.id)
        result_revoked = repository.find_by_id(already_revoked.id)
        result_other = repository.find_by_id(other.id)
        assert result_active is not None and result_active.revoked_at == now
        assert result_revoked is not None and result_revoked.revoked_at == earlier
        assert result_other is not None and result_other.revoked_at is None

    def test_deleting_an_account_deletes_its_refresh_tokens(
        self,
        repository: SqlAlchemyRefreshTokenRepository,
        db_session: Session,
        persisted_account: Account,
    ) -> None:
        token = build_refresh_token(account_id=persisted_account.id)
        repository.add(token)
        db_session.flush()

        db_session.execute(
            delete(AccountModel).where(AccountModel.id == persisted_account.id)
        )
        db_session.expire_all()

        assert repository.find_by_id(token.id) is None

    def test_update_does_not_overwrite_an_already_revoked_token(
        self,
        repository: SqlAlchemyRefreshTokenRepository,
        db_session: Session,
        persisted_account: Account,
    ) -> None:
        token = build_refresh_token(account_id=persisted_account.id)
        first_replacement = build_refresh_token(account_id=persisted_account.id)
        second_replacement = build_refresh_token(account_id=persisted_account.id)
        for refresh_token in (token, first_replacement, second_replacement):
            repository.add(refresh_token)
        db_session.flush()
        now = datetime.now(UTC)

        # Two requests both read the token while it was still active…
        winner = replace(token)
        loser = replace(token)
        winner.revoke(now, replaced_by=first_replacement.id)
        loser.revoke(now, replaced_by=second_replacement.id)

        # …only the first write is applied.
        assert repository.update(winner) is True
        assert repository.update(loser) is False

        db_session.flush()
        db_session.expire_all()
        stored = repository.find_by_id(token.id)
        assert stored is not None
        assert stored.replaced_by == first_replacement.id