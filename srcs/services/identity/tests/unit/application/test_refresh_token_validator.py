from datetime import UTC, datetime

import pytest

from src.application.port.token.types import CreatedRefreshToken
from src.application.use_cases.session.account_session import AccountSession
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.application.use_cases.session.refresh_token_validator import (
    RefreshTokenValidator,
)
from src.domain.entities.account import Account
from src.domain.entities.refresh_token import RefreshToken
from src.domain.exception import InvalidTokenError, TokenExpiredError
from tests.fixtures.security import FakeTokenService
from tests.fixtures.sessions import FakeRefreshTokenRepository


class TestRefreshTokenValidator:
    def test_return_the_stored_refresh_token(
        self,
        refresh_token_validator: RefreshTokenValidator,
        create_account_session: CreateAccountSession,
        account: Account,
    ):
        session: AccountSession = create_account_session.execute(account.id)
        stored: RefreshToken = refresh_token_validator.get_valid_refresh_token(
            session.refresh_token
        )

        assert stored.id == session.refresh_token_id
        assert stored.account_id == account.id

    def test_raises_for_an_unverifiable_token(
        self,
        refresh_token_validator: RefreshTokenValidator,
    ):
        with pytest.raises(InvalidTokenError):
            refresh_token_validator.get_valid_refresh_token("not-a-token")

    def test_raises_when_the_token_is_not_persisted(
        self,
        refresh_token_validator: RefreshTokenValidator,
        create_account_session: CreateAccountSession,
        token_service: FakeTokenService,
        account: Account,
    ):
        created: CreatedRefreshToken = token_service.create_refresh_token(account.id)

        with pytest.raises(InvalidTokenError):
            refresh_token_validator.get_valid_refresh_token(created.token)

    def test_raises_when_the_hash_does_not_match_the_stored_hash(
        self,
        refresh_token_validator: RefreshTokenValidator,
        refresh_token_repository: FakeRefreshTokenRepository,
        token_service: FakeTokenService,
        account: Account,
    ):
        created: CreatedRefreshToken = token_service.create_refresh_token(account.id)

        refresh_token_repository.add(
            RefreshToken(
                id=created.id,
                account_id=account.id,
                token_hash="a-different-hash",
                expires_at=created.expires_at,
                created_at=datetime.now(UTC),
            )
        )
        with pytest.raises(InvalidTokenError):
            refresh_token_validator.get_valid_refresh_token(created.token)

    def test_propagate_an_expired_token_error(
        self,
        refresh_token_validator: RefreshTokenValidator,
        create_account_session: CreateAccountSession,
        token_service: FakeTokenService,
        account: Account,
    ):
        session = create_account_session.execute(account.id)
        token_service.expire_refresh_token(session.refresh_token)

        with pytest.raises(TokenExpiredError):
            refresh_token_validator.get_valid_refresh_token(session.refresh_token)
