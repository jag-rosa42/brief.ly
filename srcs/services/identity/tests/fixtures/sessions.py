from dataclasses import replace
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.application.use_cases.session.account_session import AccountSession
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.application.use_cases.session.refresh_account_session import (
    RefreshAccountSession,
)
from src.application.use_cases.session.refresh_token_validator import (
    RefreshTokenValidator,
)
from src.domain.entities.refresh_token import RefreshToken
from src.domain.exception import DomainError
from tests.fixtures.security import FakeTokenService


# ---------------------------------------------------------------------------
# Refresh Token Repository
# ---------------------------------------------------------------------------
class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self._refresh_tokens_by_id: dict[UUID, RefreshToken] = {}
        self.commit_count = 0
        self.rolled_back: bool = False
        self.flushed: bool = False
        self._failure_to_raise_on_add: Exception | None = None

    def add(self, refresh_token: RefreshToken) -> None:
        if self._failure_to_raise_on_add is not None:
            raise self._failure_to_raise_on_add
        self._refresh_tokens_by_id[refresh_token.id] = refresh_token

    def update(
        self,
        refresh_token: RefreshToken,
    ) -> None:
        refresh_token_id: UUID = refresh_token.id
        stored: RefreshToken | None = self._refresh_tokens_by_id.get(refresh_token_id)
        if stored is None:
            raise ValueError(f"Refresh token {refresh_token_id} not found")
        if (
            refresh_token.replaced_by is not None
            and refresh_token.replaced_by not in self._refresh_tokens_by_id
        ):
            raise ValueError("replaced_by must reference an existing refresh token")
        stored.revoked_at = refresh_token.revoked_at
        stored.replaced_by = refresh_token.replaced_by

    def find_by_id(
        self,
        refresh_token_id: UUID,
    ) -> RefreshToken | None:
        stored = self._refresh_tokens_by_id.get(refresh_token_id)
        if stored is None:
            return None
        return replace(stored)

    def revoke_all_for_account(self, account_id: UUID, now: datetime) -> None:
        for refresh_token in self._refresh_tokens_by_id.values():
            if refresh_token.account_id == account_id and not refresh_token.is_revoked():
                refresh_token.revoke(now)

    def flush(self) -> None:
        self.flushed = True

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rolled_back = True

    @property
    def committed(self) -> bool:
        return self.commit_count > 0

    def count(self) -> int:
        return len(self._refresh_tokens_by_id)

    def get(self, refresh_token_id: UUID) -> RefreshToken:
        stored = self.find_by_id(refresh_token_id)
        assert stored is not None, f"refresh_token {refresh_token_id} was not stored"
        return stored

    def make_add_raise(self, exception: Exception) -> None:
        self._failure_to_raise_on_add = exception

    def force_expires_at(self, refresh_token_id: UUID, expires_at: datetime) -> None:
        self._refresh_tokens_by_id[refresh_token_id].expires_at = expires_at


@pytest.fixture
def refresh_token_repository() -> FakeRefreshTokenRepository:
    return FakeRefreshTokenRepository()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def build_account_session(
    access_token: str = "fake-access-token",
    refresh_token: str = "fake-refresh-token",
) -> AccountSession:
    return AccountSession(
        access_token=access_token,
        refresh_token=refresh_token,
        refresh_token_id=uuid4(),
    )


# ---------------------------------------------------------------------------
# Fake Refresh Account Session
# ---------------------------------------------------------------------------
class FakeRefreshAccountSession:
    def __init__(
        self,
        session: AccountSession | None = None,
        error: DomainError | None = None,
    ):
        self._session: AccountSession = session or build_account_session()
        self._error: DomainError | None = error
        self._execute_called_with: str | None = None

    def execute(self, refresh_token: str) -> AccountSession:
        self._execute_called_with = refresh_token
        if self._error is not None:
            raise self._error
        return self._session


# ---------------------------------------------------------------------------
# Create Account Session
# ---------------------------------------------------------------------------
@pytest.fixture
def create_account_session(
    refresh_token_repository: FakeRefreshTokenRepository,
    token_service: FakeTokenService,
) -> CreateAccountSession:
    return CreateAccountSession(refresh_token_repository, token_service)


# ---------------------------------------------------------------------------
# Refresh Token Validator
# ---------------------------------------------------------------------------
@pytest.fixture
def refresh_token_validator(
    refresh_token_repository: FakeRefreshTokenRepository,
    token_service: FakeTokenService,
) -> RefreshTokenValidator:
    return RefreshTokenValidator(refresh_token_repository, token_service)


# ---------------------------------------------------------------------------
# Refresh Account Session
# ---------------------------------------------------------------------------
@pytest.fixture
def refresh_account_session(
    refresh_token_validator: RefreshTokenValidator,
    refresh_token_repository: FakeRefreshTokenRepository,
    token_service: FakeTokenService,
    create_account_session: CreateAccountSession,
) -> RefreshAccountSession:
    return RefreshAccountSession(
        refresh_token_validator,
        refresh_token_repository,
        token_service,
        create_account_session,
    )
