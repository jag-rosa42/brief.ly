from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from src.domain.entities.account import Account
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash
from src.infrastructure.database.models.account import Account as AccountModel
from src.infrastructure.database.repositories.query import one_or_none


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
        return one_or_none(self._session, statement, self._to_domain)

    def find_by_id(self, account_id: UUID) -> Account | None:
        statement: Select[tuple[AccountModel]] = select(AccountModel).where(
            AccountModel.id == account_id
        )
        return one_or_none(self._session, statement, self._to_domain)

    def find_by_id_for_update(self, account_id: UUID) -> Account | None:
        """Load an account and lock its row until the transaction ends.

        Use SELECT ... FOR UPDATE, like the refresh tokens: a concurrent
        transaction locking the same account waits until this one commits or
        rolls back.
        populate_existing ensures the returned model contains the latest database values,
        even if it is already loaded in the session.
        """
        statement: Select[tuple[AccountModel]] = (
            select(AccountModel)
            .where(AccountModel.id == account_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return one_or_none(self._session, statement, self._to_domain)

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
