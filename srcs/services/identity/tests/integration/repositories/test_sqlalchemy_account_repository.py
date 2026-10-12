import pytest
from sqlalchemy.orm import Session

from src.domain.entities.account import Account
from src.domain.value_objects.email import Email
from src.infrastructure.database.repositories.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)


@pytest.fixture
def repository(db_session: Session) -> SqlAlchemyAccountRepository:
    return SqlAlchemyAccountRepository(db_session)


class TestSqlAlchemyAccountRepository:
    def test_save_makes_account_findable_by_email(
        self,
        repository: SqlAlchemyAccountRepository,
        db_session: Session,
        account: Account,
    ) -> None:
        # account: Account = _build_account()
        repository.save(account)
        db_session.flush()

        result: Account | None = repository.find_by_email(account.email)

        assert result is not None
        assert result.email.value == account.email.value
        assert result.id == account.id

    def test_find_by_email_returns_none_for_unknow_email(
        self,
        repository: SqlAlchemyAccountRepository,
        db_session: Session,
        account: Account,
    ) -> None:
        repository.save(account)
        db_session.flush()

        result: Account | None = repository.find_by_email(
            Email("unknown-email@example.com")
        )

        assert result is None

    def test_commit_persist_saved_account(
        self,
        repository: SqlAlchemyAccountRepository,
        db_session: Session,
        account: Account,
    ) -> None:
        repository.save(account)
        db_session.commit()

        result: Account | None = repository.find_by_email(account.email)

        assert result is not None
