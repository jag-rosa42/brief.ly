import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from src.application.port.token.types import (
    AccessTokenClaims,
    CreatedRefreshToken,
    RefreshTokenClaims,
)
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
        token_id: str | None = None,
    ) -> str:
        return jwt.encode(
            payload={
                "jti": token_id,
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

    def test_verify_access_token(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        token: str = jwt_token_service.create_access_token(account_id)

        payload: AccessTokenClaims = jwt_token_service.verify_access_token(token)

        assert isinstance(payload, AccessTokenClaims)
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
            jwt_token_service.verify_access_token(token)

    def test_raises_with_malformed_token(
        self, jwt_token_service: JWTTokenService
    ) -> None:
        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token("this-is-not-a-jwt-token")

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
            jwt_token_service.verify_access_token(token)

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
            jwt_token_service.verify_access_token(token)

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
            jwt_token_service.verify_access_token(token)

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
            jwt_token_service.verify_access_token(token)

    # ---------------------------------------------------------------------------
    # Refresh Token
    # ---------------------------------------------------------------------------

    def test_create_refresh_token(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        created_refresh_token: CreatedRefreshToken = (
            jwt_token_service.create_refresh_token(account_id)
        )

        assert isinstance(created_refresh_token, CreatedRefreshToken)
        assert created_refresh_token

        payload: dict[str, Any] = jwt.decode(
            created_refresh_token.token,
            options={"verify_signature": False},
        )

        assert payload["sub"] == str(account_id)
        assert payload["type"] == TokenType.REFRESH
        assert payload["jti"] == str(created_refresh_token.id)
        assert int(created_refresh_token.expires_at.timestamp()) == payload["exp"]

    def test_created_refresh_token_hash_is_encoded_with_sha256(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        created_refresh_token: CreatedRefreshToken = (
            jwt_token_service.create_refresh_token(account_id)
        )
        token: str = created_refresh_token.token

        assert (
            created_refresh_token.token_hash == hashlib.sha256(token.encode()).hexdigest()
        )
        assert created_refresh_token.token_hash != token

    def test_verify_refresh_token(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        created_refresh_token: CreatedRefreshToken = (
            jwt_token_service.create_refresh_token(account_id)
        )
        claims: RefreshTokenClaims = jwt_token_service.verify_refresh_token(
            created_refresh_token.token
        )

        assert isinstance(claims, RefreshTokenClaims)
        assert claims.id == created_refresh_token.id
        assert claims.account_id == account_id
        assert claims.expires_at > datetime.now(UTC)

    def test_refresh_token_outlives_access_token(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        access_token_payload: dict[str, Any] = jwt.decode(
            jwt_token_service.create_access_token(account_id),
            options={"verify_signature": False},
        )

        refresh_token_payload: dict[str, Any] = jwt.decode(
            jwt_token_service.create_refresh_token(account_id).token,
            options={"verify_signature": False},
        )

        assert refresh_token_payload["exp"] > access_token_payload["exp"]

    def test_each_refresh_token_has_unique_id(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        first: CreatedRefreshToken = jwt_token_service.create_refresh_token(account_id)
        second: CreatedRefreshToken = jwt_token_service.create_refresh_token(account_id)

        assert first.id != second.id
        assert first.token != second.token

    def test_verify_refresh_token_rejetcs_an_access_token(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        access_token: str = jwt_token_service.create_access_token(account_id)

        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_refresh_token(access_token)

    def test_verify_access_token_rejects_a_refresh_token(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        refresh_token: str = jwt_token_service.create_refresh_token(account_id).token

        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token(refresh_token)

    def test_verify_refresh_token_raises_with_expired_token(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        now: datetime = datetime.now(UTC)
        token: str = self._create_jwt_token(
            jwt_token_service,
            subject=str(account_id),
            token_type=TokenType.REFRESH,
            issued_at=now - timedelta(days=2),
            expires_at=now - timedelta(days=1),
        )

        with pytest.raises(TokenExpiredError):
            jwt_token_service.verify_refresh_token(token)

    def test_verify_refresh_token_raises_with_invalid_token_id(
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
            expires_at=now + timedelta(days=1),
            token_id="not-a-uuid",
        )

        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_refresh_token(token)
