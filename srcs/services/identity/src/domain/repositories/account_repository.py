from typing import Protocol
from uuid import UUID

from src.domain.entities.account import Account
from src.domain.value_objects.email import Email


class AccountRepository(Protocol):
    def save(self, account: Account) -> None: ...

    def find_by_email(self, email: Email) -> Account | None: ...

    def find_by_id(self, account_id: UUID) -> Account | None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
