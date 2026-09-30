import pytest

from src.application.port.token.service import TokenService
from src.application.use_cases.auth.login_account import LoginAccount
from src.application.use_cases.session.account_session import AccountSession
from src.domain.entities.account import Account
from src.domain.entities.refresh_token import RefreshToken
from src.domain.exception import InvalidCredentialsError
from tests.fixtures.accounts import FakeAccountRepository
from tests.fixtures.factory import DEFAULT_ACCOUNT_PASSWORD
from tests.fixtures.sessions import FakeRefreshTokenRepository


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

    def test_returns_account_session(
        self,
        login_account: LoginAccount,
        account_repository: FakeAccountRepository,
        account: Account,
    ) -> None:
        account_repository.save(account)

        session: AccountSession = login_account.execute(
            email=account.email.value,
            password=DEFAULT_ACCOUNT_PASSWORD,
        )
        assert session.access_token == "fake-access-token-1"
        assert session.refresh_token == "fake-refresh-token-1"

    def test_persists_refresh_token_and_commits(
        self,
        login_account: LoginAccount,
        account_repository: FakeAccountRepository,
        refresh_token_repository: FakeRefreshTokenRepository,
        token_service: TokenService,
        account: Account,
    ) -> None:
        account_repository.save(account)
        session: AccountSession = login_account.execute(
            email=account.email.value,
            password=DEFAULT_ACCOUNT_PASSWORD,
        )
        stored: RefreshToken | None = refresh_token_repository.find_by_id(
            session.refresh_token_id
        )

        assert stored is not None
        assert stored.account_id == account.id
        assert stored.token_hash == token_service.hash_token(session.refresh_token)
        assert account_repository.committed is True

    def test_does_not_create_session_for_invalid_password(
        self,
        login_account: LoginAccount,
        account_repository: FakeAccountRepository,
        refresh_token_repository: FakeRefreshTokenRepository,
        account: Account,
    ) -> None:
        account_repository.save(account)

        with pytest.raises(InvalidCredentialsError):
            login_account.execute(email=account.email.value, password="wrong-password")

        assert refresh_token_repository.count() == 0
        assert account_repository.committed is False
