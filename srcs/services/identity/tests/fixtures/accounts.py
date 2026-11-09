from uuid import UUID

import pytest

from src.application.port.password_hasher import PasswordHasher
from src.application.use_cases.auth.login_account import LoginAccount
from src.application.use_cases.auth.logout_account import LogoutAccount
from src.application.use_cases.auth.register_account import RegisterAccount
from src.application.use_cases.session.account_session import AccountSession
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.application.use_cases.session.refresh_token_validator import (
    RefreshTokenValidator,
)
from src.domain.entities.account import Account
from src.domain.exception import DomainError
from src.domain.value_objects.email import Email
from tests.fixtures.factory import (
    DEFAULT_ACCOUNT_EMAIL,
    DEFAULT_ACCOUNT_PASSWORD,
    build_account,
)
from tests.fixtures.sessions import FakeRefreshTokenRepository, build_account_session
from tests.fixtures.unit_of_work import FakeUnitOfWork

# ---------------------------------------------------------------------------
# Test Double - Fake
# ---------------------------------------------------------------------------
# Rule of thumb used in the industry: prefer fakes for anything with real
# behavior to fake (repositories, caches, gateways). Reach for mocks/spies
# only when you specifically need to verify an interaction that has no
# observable state of its own (e.g. "was the email-sending API called?").


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------


@pytest.fixture
def account(password_hasher: PasswordHasher) -> Account:
    return build_account(
        email=DEFAULT_ACCOUNT_EMAIL,
        password_hash=password_hasher.hash(DEFAULT_ACCOUNT_PASSWORD),
    )


# ---------------------------------------------------------------------------
# Account Repository
# ---------------------------------------------------------------------------
class FakeAccountRepository:
    def __init__(self) -> None:
        self._accounts_by_email: dict[str, Account] = {}
        self._accounts_by_id: dict[UUID, Account] = {}
        self._failure_to_raise_on_save: Exception | None = None
        self.locked_ids: list[UUID] = []

    def save(self, account: Account) -> None:
        if self._failure_to_raise_on_save is not None:
            raise self._failure_to_raise_on_save
        self._accounts_by_email[account.email.value] = account
        self._accounts_by_id[account.id] = account

    def find_by_email(self, email: Email) -> Account | None:
        return self._accounts_by_email.get(email.value)

    def find_by_id(self, account_id: UUID) -> Account | None:
        return self._accounts_by_id.get(account_id)

    def find_by_id_for_update(self, account_id: UUID) -> Account | None:
        # No real lock in memory: record the call so tests can check that
        # the use case asked for one.
        self.locked_ids.append(account_id)
        return self.find_by_id(account_id)

    # Helper to simulate an infrastructure failure
    def make_save_raise(self, exception: Exception) -> None:
        """Configure save() to raise the given exception."""
        self._failure_to_raise_on_save: Exception = exception


@pytest.fixture
def account_repository() -> FakeAccountRepository:
    return FakeAccountRepository()


# ---------------------------------------------------------------------------
# Fake Register Account
# ---------------------------------------------------------------------------
class FakeRegisterAccount:
    def __init__(
        self,
        session: AccountSession | None = None,
        error: DomainError | None = None,
    ) -> None:
        self._session: AccountSession = session or build_account_session()
        self._error: DomainError | None = error
        self._execute_called_with: tuple[str, str] | None = None

    def execute(self, email: str, password: str) -> AccountSession:
        self._execute_called_with: tuple[str, str] = email, password
        if self._error is not None:
            raise self._error
        return self._session


@pytest.fixture
def register_account(
    uow: FakeUnitOfWork,
    account_repository: FakeAccountRepository,
    password_hasher: PasswordHasher,
    create_account_session: CreateAccountSession,
) -> RegisterAccount:
    return RegisterAccount(
        uow,
        account_repository,
        password_hasher,
        create_account_session,
    )


# ---------------------------------------------------------------------------
# Fake Login Account
# ---------------------------------------------------------------------------
class FakeLoginAccount:
    def __init__(
        self,
        session: AccountSession | None = None,
        error: DomainError | None = None,
    ) -> None:
        self._session: AccountSession = session or build_account_session()
        self._error: DomainError | None = error
        self._execute_called_with: tuple[str, str] | None = None

    def execute(self, email: str, password: str) -> AccountSession:
        self._execute_called_with: tuple[str, str] = email, password
        if self._error is not None:
            raise self._error
        return self._session


@pytest.fixture
def login_account(
    uow: FakeUnitOfWork,
    account_repository: FakeAccountRepository,
    password_hasher: PasswordHasher,
    create_account_session: CreateAccountSession,
) -> LoginAccount:
    return LoginAccount(
        uow,
        account_repository,
        password_hasher,
        create_account_session,
    )


# ---------------------------------------------------------------------------
# Logout Account
# ---------------------------------------------------------------------------
@pytest.fixture
def logout_account(
    uow: FakeUnitOfWork,
    refresh_token_validator: RefreshTokenValidator,
    refresh_token_repository: FakeRefreshTokenRepository,
) -> LogoutAccount:
    return LogoutAccount(
        uow,
        refresh_token_validator,
        refresh_token_repository,
     )
