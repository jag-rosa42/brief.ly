import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar
from uuid import UUID, uuid4

import jwt
from jwcrypto.jwk import JWK
from pydantic import SecretStr

from src.application.port.token.types import (
    AccessTokenClaims,
    CreatedRefreshToken,
    CreatedToken,
    RefreshTokenClaims,
)
from src.domain.exception import InvalidTokenError, TokenExpiredError
from src.infrastructure.security.settings import security_settings
from src.infrastructure.security.token.jwt_payload import JWTTokenPayload
from src.infrastructure.security.token.token_type import TokenType

logger: logging.Logger = logging.getLogger(__name__)


class JWTTokenService:
    JWT_ALGORITHM: ClassVar[str] = "RS256"
    REQUIRED_CLAIMS: ClassVar[tuple[str, ...]] = (
        "iss",
        "aud",
        "jti",
        "sub",
        "type",
        "iat",
        "exp",
    )

    def __init__(self):
        self._private_key: SecretStr = security_settings.JWT_PRIVATE_KEY
        self._public_key: str = security_settings.JWT_PUBLIC_KEY
        self._algorithm: str = self.JWT_ALGORITHM
        self._issuer: str = security_settings.JWT_ISSUER
        self._key_id: str = self._compute_key_id(security_settings.JWT_PUBLIC_KEY)
        self._audiences: dict[TokenType, str] = {
            TokenType.ACCESS: security_settings.JWT_ACCESS_AUDIENCE,
            TokenType.REFRESH: security_settings.JWT_REFRESH_AUDIENCE,
        }
        self._lifetime: dict[TokenType, timedelta] = {
            TokenType.ACCESS: timedelta(
                minutes=security_settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
            TokenType.REFRESH: timedelta(
                days=security_settings.REFRESH_TOKEN_EXPIRE_DAYS
            ),
        }

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

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _create_token(self, account_id: UUID, token_type: TokenType) -> CreatedToken:
        now: datetime = datetime.now(UTC)
        token_id: UUID = uuid4()
        expires_at: datetime = now + self._lifetime[token_type]
        payload: dict[str, Any] = {
            "iss": self._issuer,
            "aud": self._audiences[token_type],
            "jti": str(token_id),  # token id
            "sub": str(account_id),  # subject
            "type": token_type,
            "iat": now,  # Issued at
            "exp": expires_at,
        }
        token: str = jwt.encode(
            payload,
            self._private_key.get_secret_value(),
            self._algorithm,
            headers={"kid": self._key_id},
        )
        return CreatedToken(id=token_id, token=token, expires_at=expires_at)

    def _decode(self, token: str, expected_type: TokenType) -> JWTTokenPayload:
        try:
            # The header is read before the signature is checked, so it is
            # only used to select the key: a token signed by a key we don't
            # know is refused immediately.
            header: dict[str, Any] = jwt.get_unverified_header(token)
            if header.get("kid") != self._key_id:
                logger.debug("Unknow token key id")
                raise InvalidTokenError()

            payload: dict[str, Any] = jwt.decode(
                jwt=token,
                key=self._public_key,
                algorithms=[self._algorithm],
                audience=self._audiences[expected_type],
                issuer=self._issuer,
                options={"require": list(self.REQUIRED_CLAIMS)},
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

    @staticmethod
    def _compute_key_id(public_key_pem: str) -> str:
        """Return the key ID (`kid`) to put in every token header.

        The `kid` is the RFC 7638 thumbprint of the public key (SHA-256,
        base64url), so it never has to be configured by hand and it changes
        whenever the key changes.

        Raises:
            ValueError: If the PEM is not a valid RSA public key. This runs at
                startup, so a bad key fails immediately rather than on a request.
        """
        public_jwk: JWK = JWK.from_pem(public_key_pem.encode())
        if public_jwk.get("kty") != "RSA":
            raise ValueError("JWT_PUBLIC_KEY must be an RSA public key")
        return public_jwk.thumbprint()