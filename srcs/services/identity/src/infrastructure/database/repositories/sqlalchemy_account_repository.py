from sqlalchemy import Result, Select, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.domain.entities.account import Account
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash
from src.infrastructure.database.models.account import Account as AccountDB


class SqlAlchemyAccountRepository:
    def __init__(self, session: Session) -> None:
        self._session: Session = session

    def save(self, account: Account) -> None:
        account_model: AccountDB = self._to_model(account)
        self._session.add(account_model)

    def find_by_email(self, email: Email) -> Account | None:
        statement: Select[tuple[AccountDB]] = select(AccountDB).where(
            AccountDB.email == email.value
        )
        result: Result[tuple[AccountDB]] = self._session.execute(statement)
        account_model: AccountDB | None = result.scalar_one_or_none()
        if account_model is None:
            return None
        return self._to_domain(account_model)

    def commit(self) -> None:
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise

    def rollback(self) -> None:
        self._session.rollback()

    @staticmethod
    def _to_domain(model: AccountDB) -> Account:
        return Account(
            id=model.id,
            email=Email(model.email),
            password_hash=PasswordHash(model.password_hash),
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(account: Account) -> AccountDB:
        email: str = account.email.value
        password_hash: str = account.password_hash.value
        return AccountDB(
            id=account.id,
            email=email,
            password_hash=password_hash,
            created_at=account.created_at,
        )
