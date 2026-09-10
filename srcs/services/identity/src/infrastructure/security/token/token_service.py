import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from pydantic import SecretStr

from src.application.port.token.types import AccessTokenPayload
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

    def create_access_token(self, account_id: UUID) -> str:
        return self._create_token(account_id, TokenType.ACCESS)

    def decode_access_token(self, token: str) -> AccessTokenPayload:
        payload: JWTTokenPayload = self._decode(token, TokenType.ACCESS)

        try:
            account_id: UUID = UUID(payload.subject)
        except ValueError as exc:
            raise InvalidTokenError() from exc
        return AccessTokenPayload(
            account_id=account_id,
            expires_at=datetime.fromtimestamp(timestamp=payload.expires_at, tz=UTC),
        )

    def _create_token(self, account_id: UUID, token_type: TokenType) -> str:
        now: datetime = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": str(account_id),  # subject
            "type": token_type,
            "iat": now,  # Issued at
            "exp": now + self._access_token_lifetime,
        }
        encoded_jwt: str = jwt.encode(
            payload,
            self._private_key.get_secret_value(),
            self._algorithm,
        )
        return encoded_jwt

    def _decode(self, token: str, expected_type: TokenType) -> JWTTokenPayload:
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self._public_key,
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
