from uuid import UUID

from sqlalchemy import Result, Select, select
from sqlalchemy.orm import Session

from src.domain.entities.account import Account
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash
from src.infrastructure.database.models.account import Account as AccountModel


class SqlAlchemyAccountRepository:
    def __init__(self, session: Session) -> None:
        self._session: Session = session

    def save(self, account: Account) -> None:
        account_model: AccountModel = self._to_model(account)
        self._session.add(account_model)

    def find_by_email(self, email: Email) -> Account | None:
        statement: Select[tuple[AccountModel]] = select(AccountModel).where(
            AccountModel.email == email.value
        )
        result: Result[tuple[AccountModel]] = self._session.execute(statement)
        account_model: AccountModel | None = result.scalar_one_or_none()
        if account_model is None:
            return None
        return self._to_domain(account_model)

    def find_by_id(self, account_id: UUID) -> Account | None:
        statement: Select[tuple[AccountModel]] = select(AccountModel).where(
            AccountModel.id == account_id
        )
        result: Result[tuple[AccountModel]] = self._session.execute(statement)
        account_model: AccountModel | None = result.scalar_one_or_none()
        if account_model is None:
            return None
        return self._to_domain(account_model)

    @staticmethod
    def _to_domain(model: AccountModel) -> Account:
        return Account(
            id=model.id,
            email=Email(model.email),
            password_hash=PasswordHash(model.password_hash),
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(account: Account) -> AccountModel:
        email: str = account.email.value
        password_hash: str = account.password_hash.value
        return AccountModel(
            id=account.id,
            email=email,
            password_hash=password_hash,
            created_at=account.created_at,
        )
