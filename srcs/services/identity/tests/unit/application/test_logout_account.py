import pytest

from src.application.use_cases.auth.logout_account import LogoutAccount
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.application.use_cases.session.refresh_account_session import (
    RefreshAccountSession,
)
from src.domain.entities.account import Account
from src.domain.exception import TokenRevokedError
from tests.fixtures.security import FakeTokenService
from tests.fixtures.sessions import FakeRefreshTokenRepository


class TestLogoutAccount:
    def test_revokes_the_refresh_token_and_commits(
        self,
        logout_account: LogoutAccount,
        create_account_session: CreateAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        account: Account,
    ) -> None:
        session = create_account_session.execute(account.id)

        logout_account.execute(session.refresh_token)

        stored = refresh_token_repository.get(session.refresh_token_id)
        assert stored.is_revoked() is True
        assert stored.replaced_by is None  # a logout is not a rotation
        assert refresh_token_repository.commit_count == 1

    def test_keeps_the_other_sessions_of_the_account_alive(
        self,
        logout_account: LogoutAccount,
        create_account_session: CreateAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        account: Account,
    ) -> None:
        first = create_account_session.execute(account.id)
        second = create_account_session.execute(account.id)

        logout_account.execute(first.refresh_token)

        assert refresh_token_repository.get(second.refresh_token_id).is_revoked() is False

    def test_is_idempotent(
        self,
        logout_account: LogoutAccount,
        create_account_session: CreateAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        account: Account,
    ) -> None:
        session = create_account_session.execute(account.id)
        logout_account.execute(session.refresh_token)
        first_revoked_at = refresh_token_repository.get(
            session.refresh_token_id
        ).revoked_at

        logout_account.execute(session.refresh_token)  # must not raise

        stored = refresh_token_repository.get(session.refresh_token_id)
        assert stored.revoked_at == first_revoked_at
        assert refresh_token_repository.commit_count == 1

    def test_ignores_an_unverifiable_token(
        self,
        logout_account: LogoutAccount,
        refresh_token_repository: FakeRefreshTokenRepository,
    ) -> None:
        logout_account.execute("not-a-token")  # must not raise

        assert refresh_token_repository.committed is False

    def test_ignores_an_expired_token(
        self,
        logout_account: LogoutAccount,
        create_account_session: CreateAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        token_service: FakeTokenService,
        account: Account,
    ) -> None:
        session = create_account_session.execute(account.id)
        token_service.expire_refresh_token(session.refresh_token)

        logout_account.execute(session.refresh_token)  # must not raise

        assert refresh_token_repository.committed is False

    def test_ignores_a_token_that_is_not_persisted(
        self,
        logout_account: LogoutAccount,
        refresh_token_repository: FakeRefreshTokenRepository,
        token_service: FakeTokenService,
        account: Account,
    ) -> None:
        created = token_service.create_refresh_token(account.id)

        logout_account.execute(created.token)

        assert refresh_token_repository.committed is False

    def test_a_logged_out_token_cannot_be_refreshed(
        self,
        logout_account: LogoutAccount,
        refresh_account_session: RefreshAccountSession,
        create_account_session: CreateAccountSession,
        account: Account,
    ) -> None:
        session = create_account_session.execute(account.id)
        logout_account.execute(session.refresh_token)

        with pytest.raises(TokenRevokedError):
            refresh_account_session.execute(session.refresh_token)

    def test_locks_the_presented_token(
        self,
        logout_account: LogoutAccount,
        create_account_session: CreateAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        account: Account,
    ) -> None:
        session = create_account_session.execute(account.id)

        logout_account.execute(session.refresh_token)

        assert refresh_token_repository.locked_ids == [session.refresh_token_id]
