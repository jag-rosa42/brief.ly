from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.application.port.password_hasher import PasswordHasher
from src.application.port.token.service import TokenService
from src.application.use_cases.login_account import LoginAccount
from src.application.use_cases.register_account import RegisterAccount
from src.domain.entities.account import Account
from src.domain.exception import DomainError
from src.domain.value_objects.email import Email

# ---------------------------------------------------------------------------
# Test Double - Fake
# ---------------------------------------------------------------------------
# Rule of thumb used in the industry: prefer fakes for anything with real
# behavior to fake (repositories, caches, gateways). Reach for mocks/spies
# only when you specifically need to verify an interaction that has no
# observable state of its own (e.g. "was the email-sending API called?").


# ---------------------------------------------------------------------------
# Account Repository
# ---------------------------------------------------------------------------
@pytest.fixture
def account(password_hasher: PasswordHasher) -> Account:
    return Account(
        id=uuid4(),
        email=Email("john-do@example.com"),
        password_hash=password_hasher.hash("secure-password"),
        created_at=datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Account Repository
# ---------------------------------------------------------------------------
class FakeAccountRepository:
    def __init__(self) -> None:
        self._accounts_by_email: dict[str, Account] = {}
        self._accounts_by_id: dict[UUID, Account] = {}
        self.committed = False
        self.rolled_back = False
        self._failure_to_raise_on_save: Exception | None = None

    def save(self, account: Account) -> None:
        if self._failure_to_raise_on_save is not None:
            raise self._failure_to_raise_on_save
        self._accounts_by_email[account.email.value] = account
        self._accounts_by_id[account.id] = account

    def find_by_email(self, email: Email) -> Account | None:
        return self._accounts_by_email.get(email.value)

    def find_by_id(self, account_id: UUID) -> Account | None:
        return self._accounts_by_id.get(account_id)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    # Helper to simulate an infrastructure failure
    def make_save_raise(self, exception: Exception) -> None:
        """Configure save() to raise the given exception."""
        self._failure_to_raise_on_save: Exception = exception


@pytest.fixture
def account_repository() -> FakeAccountRepository:
    return FakeAccountRepository()


# ---------------------------------------------------------------------------
# Register Account
# ---------------------------------------------------------------------------
class FakeRegisterAccount:
    def __init__(self, account: Account, error: DomainError | None = None) -> None:
        self._account: Account = account
        self._error: DomainError | None = error
        self._execute_called_with: tuple[str, str] | None = None

    def execute(self, email: str, password: str) -> Account:
        self._execute_called_with: tuple[str, str] = email, password
        if self._error is not None:
            raise self._error
        return self._account


@pytest.fixture
def register_account(
    account_repository: FakeAccountRepository, password_hasher: PasswordHasher
) -> RegisterAccount:
    return RegisterAccount(account_repository, password_hasher)


# ---------------------------------------------------------------------------
# Login Account
# ---------------------------------------------------------------------------
class FakeLoginAccount:
    def __init__(
        self,
        access_token: str = "fake-access-token",
        error: DomainError | None = None,
    ) -> None:
        self._access_token: str = access_token
        self._error: DomainError | None = error
        self._execute_called_with: tuple[str, str] | None = None

    def execute(self, email: str, password: str) -> str:
        self._execute_called_with: tuple[str, str] = email, password
        if self._error is not None:
            raise self._error
        return self._access_token


@pytest.fixture
def login_account(
    account_repository: FakeAccountRepository,
    password_hasher: PasswordHasher,
    token_service: TokenService,
) -> LoginAccount:
    return LoginAccount(account_repository, password_hasher, token_service)
