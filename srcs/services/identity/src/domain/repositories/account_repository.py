from typing import Protocol
from uuid import UUID

from src.domain.entities.account import Account
from src.domain.value_objects.email import Email


class AccountRepository(Protocol):
    def save(self, account: Account) -> None: ...

    def find_by_email(self, email: Email) -> Account | None: ...

    def find_by_id(self, account_id: UUID) -> Account | None: ...

    def find_by_id_for_update(self, account_id: UUID) -> Account | None:
        """
        Load an account and lock it until the transaction ends.

        A concurrent caller locking the same account waits until this transaction
        commits or rolls back. Used to serialise the checks that span several rows
        of one account (e.g. the active API key limit).
        """
        ...