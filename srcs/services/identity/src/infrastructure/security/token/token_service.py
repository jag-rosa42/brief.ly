import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from pydantic import SecretStr

from src.application.port.token.types import (
    AccessTokenClaims,
    CreatedRefreshToken,
    CreatedToken,
    RefreshTokenClaims,
)
from src.domain.exception import InvalidTokenError, TokenExpiredError
from src.infrastructure.database.config import settings
from src.infrastructure.security.token.jwt_payload import JWTTokenPayload
from src.infrastructure.security.token.token_type import TokenType

logger: logging.Logger = logging.getLogger(__name__)


class JWTTokenService:
    def __init__(self):
        self._private_key: SecretStr = settings.JWT_PRIVATE_KEY
        self._public_key: str = settings.JWT_PUBLIC_KEY
        self._algorithm: str = settings.JWT_ALGORITHM
        self._access_token_lifetime: timedelta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self._refresh_token_lifetime: timedelta = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    def create_access_token(self, account_id: UUID) -> str:
        created_token: CreatedToken = self._create_token(
            account_id,
            token_type=TokenType.ACCESS,
        )
        return created_token.token

    def verify_access_token(self, token: str) -> AccessTokenClaims:
        payload: JWTTokenPayload = self._decode(token, expected_type=TokenType.ACCESS)

        account_id: UUID = self._parse_uuid(payload.subject)
        return AccessTokenClaims(
            account_id=account_id,
            expires_at=datetime.fromtimestamp(timestamp=payload.expires_at, tz=UTC),
        )

    def create_refresh_token(self, account_id: UUID) -> CreatedRefreshToken:
        refresh_token: CreatedToken = self._create_token(
            account_id,
            token_type=TokenType.REFRESH,
        )
        return CreatedRefreshToken(
            id=refresh_token.id,
            token=refresh_token.token,
            token_hash=self.hash_token(refresh_token.token),
            expires_at=refresh_token.expires_at,
        )

    def verify_refresh_token(self, token: str) -> RefreshTokenClaims:
        payload: JWTTokenPayload = self._decode(token, expected_type=TokenType.REFRESH)

        token_id: UUID = self._parse_uuid(payload.token_id)
        account_id: UUID = self._parse_uuid(payload.subject)

        return RefreshTokenClaims(
            id=token_id,
            account_id=account_id,
            expires_at=datetime.fromtimestamp(timestamp=payload.expires_at, tz=UTC),
        )

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _create_token(self, account_id: UUID, token_type: TokenType) -> CreatedToken:
        now: datetime = datetime.now(UTC)
        token_id: UUID = uuid4()
        lifetime: timedelta = (
            self._access_token_lifetime
            if token_type == TokenType.ACCESS
            else self._refresh_token_lifetime
        )
        expires_at: datetime = now + lifetime
        payload: dict[str, Any] = {
            "jti": str(token_id),  # subject
            "sub": str(account_id),  # subject
            "type": token_type,
            "iat": now,  # Issued at
            "exp": expires_at,
        }
        token: str = jwt.encode(
            payload,
            self._private_key.get_secret_value(),
            self._algorithm,
        )
        return CreatedToken(id=token_id, token=token, expires_at=expires_at)

    def _decode(self, token: str, expected_type: TokenType) -> JWTTokenPayload:
        try:
            payload: dict[str, Any] = jwt.decode(
                jwt=token,
                key=self._public_key,
                algorithms=[self._algorithm],
                options={"require": ["sub", "type", "iat", "exp"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError() from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError() from exc

        jwt_payload: JWTTokenPayload = JWTTokenPayload.from_dict(payload)
        if jwt_payload.token_type != expected_type:
            logger.debug("Unexpected token type: expected=%s", expected_type.value)
            raise InvalidTokenError()
        return jwt_payload

    def _parse_uuid(self, value: str) -> UUID:
        try:
            return UUID(value)
        except ValueError as exc:
            raise InvalidTokenError() from exc
