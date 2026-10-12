from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.application.port.token.types import AccessTokenClaims
from src.application.use_cases.auth.logout_account import LogoutAccount
from src.application.use_cases.session.account_session import AccountSession
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.application.use_cases.session.refresh_account_session import (
    RefreshAccountSession,
)
from src.domain.entities.account import Account
from src.domain.entities.refresh_token import RefreshToken
from src.domain.exception import InvalidTokenError, TokenExpiredError, TokenRevokedError
from tests.fixtures.security import FakeTokenService
from tests.fixtures.sessions import FakeRefreshTokenRepository
from tests.fixtures.unit_of_work import FakeUnitOfWork


class TestRefreshAccountSession:
    @pytest.fixture
    def current_session(
        self,
        create_account_session: CreateAccountSession,
        account: Account,
    ) -> AccountSession:
        return create_account_session.execute(account.id)

    def test_returns_a_new_session_for_the_same_account(
        self,
        refresh_account_session: RefreshAccountSession,
        current_session: AccountSession,
        token_service: FakeTokenService,
        account: Account,
    ):
        new_session: AccountSession = refresh_account_session.execute(
            current_session.refresh_token
        )

        assert new_session.access_token != current_session.access_token
        assert new_session.refresh_token != current_session.refresh_token

        claims: AccessTokenClaims = token_service.verify_access_token(
            new_session.access_token
        )
        assert claims.account_id == account.id

    def test_rotates_the_refresh_token(
        self,
        refresh_account_session: RefreshAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        current_session: AccountSession,
    ):
        new_session: AccountSession = refresh_account_session.execute(
            current_session.refresh_token
        )
        old_refresh_tokens: RefreshToken = refresh_token_repository.get(
            current_session.refresh_token_id
        )
        new_refresh_tokens: RefreshToken = refresh_token_repository.get(
            new_session.refresh_token_id
        )
        assert old_refresh_tokens.is_revoked() is True
        assert old_refresh_tokens.replaced_by == new_session.refresh_token_id
        assert new_refresh_tokens.is_revoked() is False
        assert refresh_token_repository.count() == 2

    def test_flushed_the_new_token_before_referencing_it(
        self,
        refresh_account_session: RefreshAccountSession,
        uow: FakeUnitOfWork,
        current_session: AccountSession,
    ):
        refresh_account_session.execute(current_session.refresh_token)
        assert uow.flushed is True

    def test_commit_the_rotation_once(
        self,
        refresh_account_session: RefreshAccountSession,
        uow: FakeUnitOfWork,
        current_session: AccountSession,
    ):
        refresh_account_session.execute(current_session.refresh_token)
        assert uow.commit_count == 1

    def test_the_renew_refresh_token_can_be_rotated_again(
        self,
        refresh_account_session: RefreshAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        current_session: AccountSession,
    ):
        second_session: AccountSession = refresh_account_session.execute(
            current_session.refresh_token
        )
        third_session: AccountSession = refresh_account_session.execute(
            second_session.refresh_token
        )

        assert third_session.refresh_token not in {
            current_session.refresh_token,
            second_session.refresh_token,
        }

        assert (
            refresh_token_repository.get(second_session.refresh_token_id).replaced_by
            == third_session.refresh_token_id
        )

    def test_raises_and_changes_nothing_for_an_invalid_token(
        self,
        uow: FakeUnitOfWork,
        refresh_account_session: RefreshAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        create_account_session: CreateAccountSession,
        account: Account,
    ):
        create_account_session.execute(account.id)

        with pytest.raises(InvalidTokenError):
            refresh_account_session.execute("not-a-token")

        assert refresh_token_repository.count() == 1
        assert uow.committed is False

    def test_raises_when_the_stored_token_is_expired(
        self,
        uow: FakeUnitOfWork,
        refresh_account_session: RefreshAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        current_session: AccountSession,
    ):
        refresh_token_repository.force_expires_at(
            current_session.refresh_token_id,
            datetime.now(UTC) - timedelta(seconds=1),
        )

        with pytest.raises(TokenExpiredError):
            refresh_account_session.execute(current_session.refresh_token)

        assert refresh_token_repository.count() == 1
        assert uow.committed is False
        assert (
            refresh_token_repository.get(current_session.refresh_token_id).is_revoked()
            is False
        )

    def test_reusing_a_rotated_token_raises(
        self,
        refresh_account_session: RefreshAccountSession,
        current_session: AccountSession,
    ):
        refresh_account_session.execute(current_session.refresh_token)
        with pytest.raises(TokenRevokedError):
            refresh_account_session.execute(current_session.refresh_token)

    def test_reuse_revokes_every_token_of_the_account(
        self,
        refresh_account_session: RefreshAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        current_session: AccountSession,
    ):
        new_session: AccountSession = refresh_account_session.execute(
            current_session.refresh_token
        )

        with pytest.raises(TokenRevokedError):
            refresh_account_session.execute(current_session.refresh_token)

        assert refresh_token_repository.get(new_session.refresh_token_id).is_revoked()

        with pytest.raises(TokenRevokedError):
            refresh_account_session.execute(new_session.refresh_token)

    def test_reuse_persists_the_revocation_before_raising(
        self,
        refresh_account_session: RefreshAccountSession,
        uow: FakeUnitOfWork,
        current_session: AccountSession,
    ):
        refresh_account_session.execute(current_session.refresh_token)
        with pytest.raises(TokenRevokedError):
            refresh_account_session.execute(current_session.refresh_token)

        assert uow.commit_count == 2

    def test_reuse_does_not_touch_other_accounts(
        self,
        refresh_account_session: RefreshAccountSession,
        create_account_session: CreateAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        current_session: AccountSession,
    ):
        other_session = create_account_session.execute(uuid4())
        refresh_account_session.execute(current_session.refresh_token)

        with pytest.raises(TokenRevokedError):
            refresh_account_session.execute(current_session.refresh_token)

        other = refresh_token_repository.get(other_session.refresh_token_id)

        assert other.is_revoked() is False

    def test_reusing_a_logged_out_token_raises(
        self,
        refresh_account_session: RefreshAccountSession,
        logout_account: LogoutAccount,
        current_session: AccountSession,
    ) -> None:
        logout_account.execute(current_session.refresh_token)

        with pytest.raises(TokenRevokedError):
            refresh_account_session.execute(current_session.refresh_token)

    def test_reusing_a_logged_out_token_keeps_the_other_sessions_alive(
        self,
        refresh_account_session: RefreshAccountSession,
        logout_account: LogoutAccount,
        create_account_session: CreateAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        current_session: AccountSession,
        account: Account,
    ) -> None:
        other_device = create_account_session.execute(account.id)
        logout_account.execute(current_session.refresh_token)

        with pytest.raises(TokenRevokedError):
            refresh_account_session.execute(current_session.refresh_token)

        assert (
            refresh_token_repository.get(other_device.refresh_token_id).is_revoked()
            is False
        )
        # we still rotate normally
        refresh_account_session.execute(other_device.refresh_token)

    def test_reusing_a_logged_out_token_does_not_commit_anything(
        self,
        refresh_account_session: RefreshAccountSession,
        logout_account: LogoutAccount,
        uow: FakeUnitOfWork,
        current_session: AccountSession,
    ) -> None:
        logout_account.execute(current_session.refresh_token)  # commit 1
        assert uow.commit_count == 1

        with pytest.raises(TokenRevokedError):
            refresh_account_session.execute(current_session.refresh_token)

        assert uow.commit_count == 1  # no additional commit

    def test_rolls_back_when_session_creation_fails(
        self,
        refresh_account_session: RefreshAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        uow: FakeUnitOfWork,
        current_session: AccountSession,
    ):
        refresh_token_repository.make_add_raise(RuntimeError("connection lost"))

        with pytest.raises(RuntimeError, match="connection lost"):
            refresh_account_session.execute(current_session.refresh_token)

        assert uow.committed is False
        assert uow.rolled_back is True
        stored = refresh_token_repository.get(current_session.refresh_token_id)
        assert stored.is_revoked() is False
