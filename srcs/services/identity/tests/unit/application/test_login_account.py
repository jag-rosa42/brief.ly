import pytest

from src.application.use_cases.login_account import LoginAccount
from src.domain.entities.account import Account
from src.domain.exception import InvalidCredentialsError
from tests.fixtures.accounts import FakeAccountRepository


class TestLoginAccount:
    def test_raises_for_unknown_email(
        self,
        login_account: LoginAccount,
    ) -> None:
        with pytest.raises(InvalidCredentialsError):
            login_account.execute(
                email="unknown@example.com",
                password="secure-password",
            )

    def test_raises_for_invalid_password(
        self,
        login_account: LoginAccount,
        account_repository: FakeAccountRepository,
        account: Account,
    ) -> None:
        account_repository.save(account)
        with pytest.raises(InvalidCredentialsError):
            login_account.execute(
                email=account.email.value,
                password="wrong-password",
            )

    def test_returns_access_token(
        self,
        login_account: LoginAccount,
        account_repository: FakeAccountRepository,
        account: Account,
    ) -> None:
        account_repository.save(account)
        token: str = login_account.execute(
            email=account.email.value,
            password="secure-password",
        )
        assert token == "fake-access-token-1"
