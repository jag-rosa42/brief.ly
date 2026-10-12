import datetime
from uuid import UUID, uuid4

import pytest

from src.application.use_cases.auth.register_account import RegisterAccount
from src.application.use_cases.session.account_session import AccountSession
from src.domain.entities.account import Account
from src.domain.entities.refresh_token import RefreshToken
from src.domain.exception import EmailAlreadyRegisteredError
from src.domain.repositories.account_repository import AccountRepository
from src.domain.value_objects.email import Email
from tests.fixtures.accounts import FakeAccountRepository
from tests.fixtures.security import FakePasswordHasher, FakeTokenService
from tests.fixtures.sessions import FakeRefreshTokenRepository
from tests.fixtures.unit_of_work import FakeUnitOfWork


class TestRegisterAccount:
    def test_registers_new_account_with_hashed_password(
        self,
        register_account: RegisterAccount,
        account_repository: FakeAccountRepository,
    ) -> None:
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        register_account.execute(email, plaintext_password)
        account: Account | None = account_repository.find_by_email(Email(email))

        assert account is not None
        assert account.email.value == email
        assert account.password_hash.value == f"hashed::{plaintext_password}"
        assert isinstance(account.id, UUID)

    def test_persists_and_commits_new_account(
        self,
        register_account: RegisterAccount,
        account_repository: FakeAccountRepository,
        uow: FakeUnitOfWork,
    ) -> None:
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        register_account.execute(email, plaintext_password)
        stored_account: Account | None = account_repository.find_by_email(Email(email))

        assert stored_account is not None
        assert uow.commit_count == 1

    def test_returns_session_linked_to_registered_account(
        self,
        register_account: RegisterAccount,
        account_repository: AccountRepository,
        refresh_token_repository: FakeRefreshTokenRepository,
        token_service: FakeTokenService,
    ):
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        session: AccountSession = register_account.execute(email, plaintext_password)
        account: Account | None = account_repository.find_by_email(Email(email))
        stored: RefreshToken | None = refresh_token_repository.find_by_id(
            session.refresh_token_id
        )

        assert account is not None
        assert (
            token_service.verify_access_token(session.access_token).account_id
            == account.id
        )
        assert stored is not None
        assert stored.account_id == account.id

    def test_raises_when_email_is_already_registered(
        self,
        register_account: RegisterAccount,
        account_repository: FakeAccountRepository,
        password_hasher: FakePasswordHasher,
    ) -> None:
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        account: Account = Account(
            id=uuid4(),
            email=Email(email),
            password_hash=password_hasher.hash(plaintext_password),
            created_at=datetime.datetime.now(datetime.UTC),
        )
        account_repository.save(account)
        with pytest.raises(EmailAlreadyRegisteredError):
            register_account.execute(email, f"{plaintext_password}-2")

    def test_rollback_and_raises_on_unicity_email_constraint_violation(
        self,
        register_account: RegisterAccount,
        uow: FakeUnitOfWork,
    ) -> None:
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        # simulate a DB-level failure ( lost connetcion, constraint violation, etc.)
        uow.make_commit_raise(EmailAlreadyRegisteredError())
        with pytest.raises(EmailAlreadyRegisteredError):
            register_account.execute(email, plaintext_password)

        assert uow.committed is False
        assert uow.rolled_back is True

    def test_does_not_touch_repository_when_email_is_already_registered(
        self,
        register_account: RegisterAccount,
        account_repository: FakeAccountRepository,
        refresh_token_repository: FakeRefreshTokenRepository,
        uow: FakeUnitOfWork,
        password_hasher: FakePasswordHasher,
    ) -> None:
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        account: Account = Account(
            id=uuid4(),
            email=Email(email),
            password_hash=password_hasher.hash(plaintext_password),
            created_at=datetime.datetime.now(datetime.UTC),
        )
        account_repository.save(account)
        with pytest.raises(EmailAlreadyRegisteredError):
            register_account.execute(email, f"{plaintext_password}-2")

        assert uow.committed is False
        assert refresh_token_repository.count() == 0

    def test_rollback_and_raises_when_session_creation_fails(
        self,
        register_account: RegisterAccount,
        account_repository: FakeAccountRepository,
        refresh_token_repository: FakeRefreshTokenRepository,
        uow: FakeUnitOfWork,
    ) -> None:
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        refresh_token_repository.make_add_raise(RuntimeError("connection lost"))

        with pytest.raises(RuntimeError, match="connection lost"):
            register_account.execute(email, plaintext_password)

        assert uow.committed is False
        assert uow.rolled_back is True

    def test_rollback_and_raises_when_account_repository_save_fails(
        self,
        register_account: RegisterAccount,
        account_repository: FakeAccountRepository,
        uow: FakeUnitOfWork,
    ) -> None:
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        # simulate a DB-level failure ( lost connetcion, constraint violation, etc.)
        account_repository.make_save_raise(RuntimeError("connection lost"))
        with pytest.raises(RuntimeError, match="connection lost"):
            register_account.execute(email, plaintext_password)

        assert uow.committed is False
        assert uow.rolled_back is True

    @pytest.mark.parametrize(
        argnames="email, password",
        argvalues=[
            ("john.doe10@example.com", "secure-password1!"),
            ("john.doe20@example.com", "secure-password2!"),
            ("john.doe30@example.com", "secure-password3!"),
        ],
    )
    def test_registers_several_distinct_accounts(
        self,
        register_account: RegisterAccount,
        account_repository: FakeAccountRepository,
        email: str,
        password: str,
    ) -> None:
        register_account.execute(email, password)
        account = account_repository.find_by_email(Email(email))

        assert account is not None
        assert account.email.value == email
