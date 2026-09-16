from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.application.port.token.types import AccessTokenPayload
from src.domain.exception import InvalidTokenError, TokenExpiredError
from src.domain.value_objects.password_hash import PasswordHash
from src.infrastructure.security.token.token_service import JWTTokenService


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
# Token Service
# ---------------------------------------------------------------------------


class FakeTokenService:
    def __init__(self) -> None:
        self._tokens: dict[str, AccessTokenPayload] = {}
        self._token_count: int = 0
        self._expires_in: timedelta = timedelta(minutes=5)

    def create_access_token(self, account_id: UUID) -> str:
        self._token_count += 1
        token = f"fake-access-token-{self._token_count}"

        self._tokens[token] = AccessTokenPayload(
            account_id=account_id, expires_at=datetime.now(UTC) + self._expires_in
        )
        return token

    def decode_access_token(self, token: str) -> AccessTokenPayload:
        access_token_payload: AccessTokenPayload | None = self._tokens.get(token)

        if access_token_payload is None:
            raise InvalidTokenError()
        if access_token_payload.expires_at <= datetime.now(UTC):
            raise TokenExpiredError()
        return access_token_payload


@pytest.fixture
def token_service() -> FakeTokenService:
    return FakeTokenService()


@pytest.fixture
def jwt_token_service() -> JWTTokenService:
    return JWTTokenService()
