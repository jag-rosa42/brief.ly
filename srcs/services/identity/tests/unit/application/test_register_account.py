import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from src.application.use_cases.register_account import RegisterAccount
from src.domain.entities.account import Account
from src.domain.exception import EmailAlreadyRegisteredError
from src.domain.value_objects.email import Email
from tests.fixtures.accounts import FakeAccountRepository
from tests.fixtures.security import FakePasswordHasher


class TestRegisterAccount:
    def test_registers_new_account_with_hashed_password(
        self,
        register_account: RegisterAccount,
    ) -> None:
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        account: Account = register_account.execute(email, plaintext_password)

        assert account.email.value == email
        assert account.password_hash.value == f"hashed::{plaintext_password}"
        assert isinstance(account.id, UUID)

    def test_persists_and_commits_new_account(
        self,
        register_account: RegisterAccount,
        account_repository: FakeAccountRepository,
    ) -> None:
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        account: Account = register_account.execute(email, plaintext_password)
        stored_account: Account | None = account_repository.find_by_email(Email(email))

        assert account == stored_account
        assert account_repository.committed is True
        assert account_repository.rolled_back is False

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
        account_repository: FakeAccountRepository,
    ) -> None:
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        # simulate a DB-level failure ( lost connetcion, constraint violation, etc.)
        account_repository.make_save_raise(
            IntegrityError(
                "duplicate key value violates unique constraint",
                None,
                Exception("uq_accounts_email"),
            )
        )
        with pytest.raises(EmailAlreadyRegisteredError):
            register_account.execute(email, plaintext_password)

        assert account_repository.rolled_back is True
        assert account_repository.committed is False

    def test_does_not_touch_repository_when_email_is_already_registered(
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

        assert account_repository.committed is False

    def test_rollback_and_raises_when_saved_failed(
        self,
        register_account: RegisterAccount,
        account_repository: FakeAccountRepository,
    ) -> None:
        email: str = "john.doe@example.com"
        plaintext_password: str = "secure-password"

        # simulate a DB-level failure ( lost connetcion, constraint violation, etc.)
        account_repository.make_save_raise(RuntimeError("connection lost"))
        with pytest.raises(RuntimeError, match="connection lost"):
            register_account.execute(email, plaintext_password)

        assert account_repository.rolled_back is True
        assert account_repository.committed is False

    @pytest.mark.parametrize(
        argnames="email, password",
        argvalues=[
            ("john.doe10@example.com", "secure-password1!"),
            ("john.doe20@example.com", "secure-password2!"),
            ("john.doe30@example.com", "secure-password3!"),
        ],
    )
    def test_registers_several_distinct_accounts(
        self, register_account: RegisterAccount, email: str, password: str
    ) -> None:
        account: Account = register_account.execute(email, password)
        assert account.email.value == email
