from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from src.application.port.token.types import (
    AccessTokenClaims,
    CreatedRefreshToken,
    RefreshTokenClaims,
)
from src.domain.exception import InvalidTokenError, TokenExpiredError
from src.domain.value_objects.password_hash import PasswordHash
from src.infrastructure.security.token.token_service import JWTTokenService

# from src.infrastructure.security.token.token_service import JWTTokenService


# ---------------------------------------------------------------------------
# Password Hasher
# ---------------------------------------------------------------------------
class FakePasswordHasher:
    PREFIX = "hashed::"

    def hash(self, plaintext: str) -> PasswordHash:
        return PasswordHash(f"{self.PREFIX}{plaintext}")

    def verify(self, plaintext: str, password_hash: PasswordHash) -> bool:
        return password_hash.value == f"{self.PREFIX}{plaintext}"


@pytest.fixture
def password_hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


# ---------------------------------------------------------------------------
# Token Hasher
# ---------------------------------------------------------------------------
class FakeTokenHasher:
    """Readable hashes, so a failing test shows what was hashed."""

    PREFIX = "hashed::"

    def hash(self, token: str) -> str:
        return f"{self.PREFIX}{token}"


@pytest.fixture
def token_hasher() -> FakeTokenHasher:
    return FakeTokenHasher()


# ---------------------------------------------------------------------------
# Fake Token Service
# ---------------------------------------------------------------------------


class FakeTokenService:
    def __init__(self) -> None:
        self._access_tokens: dict[str, AccessTokenClaims] = {}
        self._refresh_tokens: dict[str, RefreshTokenClaims] = {}
        self._access_token_count: int = 0
        self._refresh_token_count: int = 0
        self._access_token_lifetime: timedelta = timedelta(minutes=5)
        self._refresh_token_lifetime: timedelta = timedelta(days=7)

    def create_access_token(self, account_id: UUID) -> str:
        self._access_token_count += 1
        token = f"fake-access-token-{self._access_token_count}"

        self._access_tokens[token] = AccessTokenClaims(
            account_id=account_id,
            expires_at=datetime.now(UTC) + self._access_token_lifetime,
        )
        return token

    def verify_access_token(self, token: str) -> AccessTokenClaims:
        claims: AccessTokenClaims | None = self._access_tokens.get(token)

        if claims is None:
            raise InvalidTokenError()
        if claims.expires_at <= datetime.now(UTC):
            raise TokenExpiredError()
        return claims

    def create_refresh_token(self, account_id: UUID) -> CreatedRefreshToken:
        self._refresh_token_count += 1
        token = f"fake-refresh-token-{self._refresh_token_count}"
        token_id = uuid4()
        expires_at = datetime.now(UTC) + self._refresh_token_lifetime

        self._refresh_tokens[token] = RefreshTokenClaims(
            id=token_id, account_id=account_id, expires_at=expires_at
        )

        return CreatedRefreshToken(
            id=token_id,
            token=token,
            expires_at=expires_at,
        )

    def verify_refresh_token(self, token: str) -> RefreshTokenClaims:
        claims: RefreshTokenClaims | None = self._refresh_tokens.get(token)
        if claims is None:
            raise InvalidTokenError()
        if claims.expires_at <= datetime.now(UTC):
            raise TokenExpiredError()
        return claims

    def expire_refresh_token(self, token: str) -> None:
        """Test helper: the token service now considers this refresh token expired."""
        claims = self._refresh_tokens[token]
        self._refresh_tokens[token] = replace(
            claims, expires_at=datetime.now(UTC) - timedelta(seconds=1)
        )


@pytest.fixture
def token_service() -> FakeTokenService:
    return FakeTokenService()


# ---------------------------------------------------------------------------
# Real JWT Token Service
# ---------------------------------------------------------------------------
@pytest.fixture
def jwt_token_service() -> JWTTokenService:
    # from src.infrastructure.security.token.token_service import JWTTokenService

    return JWTTokenService()
