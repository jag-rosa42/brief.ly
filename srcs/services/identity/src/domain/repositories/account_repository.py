from typing import Protocol

from src.domain.entities.account import Account
from src.domain.value_objects.email import Email


class AccountRepository(Protocol):
    def save(self, account: Account) -> None: ...

    def find_by_email(self, email: Email) -> Account | None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
