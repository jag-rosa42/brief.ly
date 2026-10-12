import pytest
from sqlalchemy.orm import Session

from src.application.port.password_hasher import PasswordHasher
from src.domain.entities.account import Account
from src.domain.exception import EmailAlreadyRegisteredError
from src.domain.value_objects.email import Email
from src.infrastructure.database.repositories.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)
from src.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from tests.fixtures.factory import (
    DEFAULT_ACCOUNT_EMAIL,
    DEFAULT_ACCOUNT_PASSWORD,
    build_account,
)


class TestSqlAlchemyUnitOfWork:
    def test_commit_persists_staged_changes(
        self,
        db_session: Session,
        account: Account,
    ) -> None:
        uow = SqlAlchemyUnitOfWork(db_session)
        repository = SqlAlchemyAccountRepository(db_session)

        with uow:
            repository.save(account)
            uow.commit()

        assert repository.find_by_id(account.id) is not None

    def test_leaving_the_block_without_commit_discards_changes(
        self,
        db_session: Session,
        account: Account,
    ) -> None:
        uow = SqlAlchemyUnitOfWork(db_session)
        repository = SqlAlchemyAccountRepository(db_session)

        with uow:
            repository.save(account)

        assert repository.find_by_id(account.id) is None

    def test_an_exception_discards_changes(
        self,
        db_session: Session,
        account: Account,
    ) -> None:
        uow = SqlAlchemyUnitOfWork(db_session)
        repository = SqlAlchemyAccountRepository(db_session)

        with pytest.raises(RuntimeError), uow:
            repository.save(account)
            raise RuntimeError("boom")

        assert repository.find_by_id(account.id) is None

    def test_commit_translates_the_email_unique_violation(
        self,
        db_session: Session,
        password_hasher: PasswordHasher,
    ) -> None:
        uow = SqlAlchemyUnitOfWork(db_session)
        repository = SqlAlchemyAccountRepository(db_session)
        password_hash = password_hasher.hash(DEFAULT_ACCOUNT_PASSWORD)

        with uow:
            repository.save(
                build_account(email=DEFAULT_ACCOUNT_EMAIL, password_hash=password_hash)
            )
            uow.commit()

        with pytest.raises(EmailAlreadyRegisteredError), uow:
            repository.save(
                build_account(email=DEFAULT_ACCOUNT_EMAIL, password_hash=password_hash)
            )
            uow.commit()

        # The first account is still there, the session is usable again.
        assert repository.find_by_email(Email(DEFAULT_ACCOUNT_EMAIL)) is not None
