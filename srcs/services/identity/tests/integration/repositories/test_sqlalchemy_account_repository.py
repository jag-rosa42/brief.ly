import datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.domain.entities.account import Account
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash
from src.infrastructure.database.repositories.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)

VALID_EMAIL: str = "john.doe@example.com"
VALID_PASSWORD: str = "super-secret"


def _build_account(email: str = VALID_EMAIL, password: str = VALID_PASSWORD) -> Account:
    return Account(
        id=uuid4(),
        email=Email(email),
        password_hash=PasswordHash(password),
        created_at=datetime.datetime.now(datetime.UTC),
    )


@pytest.fixture
def repository(db_session: Session) -> SqlAlchemyAccountRepository:
    return SqlAlchemyAccountRepository(db_session)


class TestSqlAlchemyAccountRepository:
    def test_save_makes_account_findable_by_email(
        self, repository: SqlAlchemyAccountRepository, db_session: Session
    ) -> None:
        account: Account = _build_account()
        repository.save(account)
        db_session.flush()

        result: Account | None = repository.find_by_email(Email(VALID_EMAIL))

        assert result is not None
        assert result.email.value == VALID_EMAIL
        assert result.id == account.id

    def test_find_by_email_returns_none_for_unknow_email(
        self, repository: SqlAlchemyAccountRepository, db_session: Session
    ) -> None:
        account: Account = _build_account()
        repository.save(account)
        db_session.flush()

        result: Account | None = repository.find_by_email(
            Email("unknown-email@example.com")
        )

        assert result is None

    def test_commit_persist_saved_account(
        self, repository: SqlAlchemyAccountRepository, db_session: Session
    ) -> None:
        account: Account = _build_account()
        repository.save(account)
        db_session.commit()

        result: Account | None = repository.find_by_email(Email(VALID_EMAIL))

        assert result is not None

    def test_commit_rollback_on_integrity_violation(
        self, repository: SqlAlchemyAccountRepository, db_session: Session
    ) -> None:
        account1: Account = _build_account()
        repository.save(account1)
        db_session.commit()

        account2: Account = _build_account()
        repository.save(account2)

        with pytest.raises(SQLAlchemyError):
            db_session.commit()
        repository.rollback()

        result: Account | None = repository.find_by_email(Email(VALID_EMAIL))
        assert result is not None

    def test_rollback_discard_unsaved_changes(
        self, repository: SqlAlchemyAccountRepository, db_session: Session
    ) -> None:
        account: Account = _build_account()
        repository.save(account)
        repository.rollback()

        result: Account | None = repository.find_by_email(Email(VALID_EMAIL))

        assert result is None
