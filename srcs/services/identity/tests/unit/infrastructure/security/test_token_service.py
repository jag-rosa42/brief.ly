from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from src.application.port.token.types import AccessTokenPayload
from src.domain.entities.account import Account
from src.domain.exception import InvalidTokenError, TokenExpiredError
from src.infrastructure.security.token.token_service import JWTTokenService
from src.infrastructure.security.token.token_type import TokenType


class TestJWTTokenService:
    @pytest.fixture
    def account_id(self, account: Account) -> UUID:
        return account.id

    def _create_jwt_token(
        self,
        token_service: JWTTokenService,
        *,
        subject: str,
        token_type: TokenType,
        issued_at: datetime,
        expires_at: datetime,
    ) -> str:
        return jwt.encode(
            payload={
                "sub": subject,
                "type": token_type,
                "iat": issued_at,
                "exp": expires_at,
            },
            key=token_service._private_key.get_secret_value(),
            algorithm=token_service._algorithm,
        )

    def test_create_access_token(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        token: str = jwt_token_service.create_access_token(account_id)

        assert isinstance(token, str)
        assert token

        # Decode the token to extract the payload,
        # but we don't need to verify that it was actually signed with the expected key.
        payload: dict[str, Any] = jwt.decode(
            token,
            options={"verify_signature": False},
        )

        assert payload["sub"] == str(account_id)
        assert payload["type"] == TokenType.ACCESS
        assert "iat" in payload
        assert "exp" in payload

    def test_decode_access_token(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        token: str = jwt_token_service.create_access_token(account_id)

        payload: AccessTokenPayload = jwt_token_service.decode_access_token(token)

        assert isinstance(payload, AccessTokenPayload)
        assert payload.account_id == account_id
        assert payload.expires_at > datetime.now(UTC)

    def test_raises_with_expired_token(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        now: datetime = datetime.now(UTC)

        token: str = self._create_jwt_token(
            jwt_token_service,
            subject=str(account_id),
            token_type=TokenType.ACCESS,
            issued_at=now - timedelta(minutes=10),
            expires_at=now - timedelta(minutes=5),
        )
        with pytest.raises(TokenExpiredError):
            jwt_token_service.decode_access_token(token)

    def test_raises_with_malformed_token(
        self, jwt_token_service: JWTTokenService
    ) -> None:
        with pytest.raises(InvalidTokenError):
            jwt_token_service.decode_access_token("this-is-not-a-jwt-token")

    def test_raises_with_wrong_token_type(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        now: datetime = datetime.now(UTC)

        token: str = self._create_jwt_token(
            jwt_token_service,
            subject=str(account_id),
            token_type=TokenType.REFRESH,
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )
        with pytest.raises(InvalidTokenError):
            jwt_token_service.decode_access_token(token)

    def test_raises_with_invalid_subject(
        self,
        jwt_token_service: JWTTokenService,
    ) -> None:
        now: datetime = datetime.now(UTC)

        token: str = self._create_jwt_token(
            jwt_token_service,
            subject="not-a-UUID",
            token_type=TokenType.ACCESS,
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )

        with pytest.raises(InvalidTokenError):
            jwt_token_service.decode_access_token(token)

    def test_raises_with_wrong_token_key(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        now: datetime = datetime.now(UTC)
        payload: dict[str, str | datetime] = {
            "sub": str(account_id),
            "type": TokenType.ACCESS,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        # source : https://cryptography.io/en/stable/hazmat/primitives/asymmetric/rsa/
        wrong_private_key: RSAPrivateKey = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        token: str = jwt.encode(
            payload,
            key=wrong_private_key,
            algorithm=jwt_token_service._algorithm,
        )
        with pytest.raises(InvalidTokenError):
            jwt_token_service.decode_access_token(token)

    def test_raises_with_missing_claim(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        now: datetime = datetime.now(UTC)
        payload: dict[str, str | datetime] = {
            "sub": str(account_id),
            "type": TokenType.ACCESS,
            "iat": now,
            # exp is intentianally missing
        }
        token: str = jwt.encode(
            payload,
            key=jwt_token_service._private_key.get_secret_value(),
            algorithm=jwt_token_service._algorithm,
        )
        with pytest.raises(InvalidTokenError):
            jwt_token_service.decode_access_token(token)
