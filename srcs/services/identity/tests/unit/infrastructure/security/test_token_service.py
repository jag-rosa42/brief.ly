from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

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
from src.infrastructure.security.settings import security_settings
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
        overrides: dict[str, Any] | None = None,
        missing: tuple[str, ...] = (),
        headers: dict[str, Any] | None = None,
        key: Any = None,
    ) -> str:
        """Build a token by hand, valid by default, so each test breaks one thing.

        overrides: replace claims (e.g. a wrong issuer)
        missing:   remove claims
        headers:   replace the default header (which carries the right kid)
        key:       sign with another private key
        """
        audience: str = (
            security_settings.JWT_ACCESS_AUDIENCE
            if token_type == TokenType.ACCESS
            else security_settings.JWT_REFRESH_AUDIENCE
        )
        payload: dict[str, Any] = {
            "iss": security_settings.JWT_ISSUER,
            "aud": audience,
            "jti": token_id or str(uuid4()),
            "sub": subject,
            "type": token_type,
            "iat": issued_at,
            "exp": expires_at,
        }
        payload.update(overrides or {})
        for claim in missing:
            payload.pop(claim)

        return jwt.encode(
            payload=payload,
            key=key or token_service._private_key.get_secret_value(),
            algorithm=token_service._algorithm,
            headers=headers if headers is not None else {"kid": token_service._key_id},
        )

    def _valid_access_token(
        self,
        token_service: JWTTokenService,
        account_id: UUID,
        **kwargs: Any,
    ) -> str:
        now: datetime = datetime.now(UTC)
        return self._create_jwt_token(
            token_service,
            subject=str(account_id),
            token_type=TokenType.ACCESS,
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
            **kwargs,
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
        # Right kid in the header, but signed with another private key.
        wrong_private_key: RSAPrivateKey = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        token: str = self._valid_access_token(
            jwt_token_service, account_id, key=wrong_private_key
        )
        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token(token)

    @pytest.mark.parametrize("claim", JWTTokenService.REQUIRED_CLAIMS)
    def test_raises_with_missing_claim(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
        claim: str,
    ) -> None:
        token: str = self._valid_access_token(
            jwt_token_service,
            account_id,
            missing=(claim,),
        )

        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token(token)

    def test_access_token_carries_issuer_and_api_audience(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        payload: dict[str, Any] = jwt.decode(
            jwt_token_service.create_access_token(account_id),
            options={"verify_signature": False},
        )

        assert payload["iss"] == security_settings.JWT_ISSUER
        assert payload["aud"] == security_settings.JWT_ACCESS_AUDIENCE

    def test_access_token_header_carries_rs256_and_key_id(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        header: dict[str, Any] = jwt.get_unverified_header(
            jwt_token_service.create_access_token(account_id)
        )

        assert header["alg"] == "RS256"
        assert header["kid"] == JWTTokenService._compute_key_id(
            security_settings.JWT_PUBLIC_KEY
        )

    def test_access_token_lifetime_follows_settings(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        payload: dict[str, Any] = jwt.decode(
            jwt_token_service.create_access_token(account_id),
            options={"verify_signature": False},
        )

        expected: int = security_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert payload["exp"] - payload["iat"] == expected

    def test_raises_with_wrong_issuer(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        token: str = self._valid_access_token(
            jwt_token_service, account_id, overrides={"iss": "someone-else"}
        )
        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token(token)

    def test_raises_with_wrong_audience(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        token: str = self._valid_access_token(
            jwt_token_service,
            account_id,
            overrides={"aud": "transcendence:public-api"},
        )
        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token(token)

    @pytest.mark.parametrize(
        "audience",
        [
            [security_settings.JWT_ACCESS_AUDIENCE],
            [security_settings.JWT_ACCESS_AUDIENCE, "transcendence:public-api"],
        ],
    )
    def test_raises_with_audience_list(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
        audience: list[str],
    ) -> None:
        # PyJWT accepts a list that contains the expected audience, so only
        # JWTTokenPayload enforces "one token, one audience".
        token: str = self._valid_access_token(
            jwt_token_service, account_id, overrides={"aud": audience}
        )
        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token(token)

    def test_raises_with_unknown_key_id(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        token: str = self._valid_access_token(
            jwt_token_service, account_id, headers={"kid": "unknown-key"}
        )
        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token(token)

    def test_raises_without_key_id(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        token: str = self._valid_access_token(jwt_token_service, account_id, headers={})
        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token(token)

    def test_raises_with_alg_none(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        # An unsigned token: if the verifier trusted the token's own "alg"
        # header, anybody could forge one.
        now: datetime = datetime.now(UTC)
        token: str = jwt.encode(
            payload={
                "iss": security_settings.JWT_ISSUER,
                "aud": security_settings.JWT_ACCESS_AUDIENCE,
                "jti": str(uuid4()),
                "sub": str(account_id),
                "type": TokenType.ACCESS,
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            key="",
            algorithm="none",
            headers={"kid": jwt_token_service._key_id},
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

    def test_refresh_token_carries_issuer_and_identity_audience(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        created: CreatedRefreshToken = jwt_token_service.create_refresh_token(account_id)

        payload: dict[str, Any] = jwt.decode(
            created.token, options={"verify_signature": False}
        )

        assert payload["iss"] == security_settings.JWT_ISSUER
        assert payload["aud"] == security_settings.JWT_REFRESH_AUDIENCE


    def test_refresh_token_lifetime_follows_settings(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        created: CreatedRefreshToken = jwt_token_service.create_refresh_token(account_id)

        payload: dict[str, Any] = jwt.decode(
            created.token, options={"verify_signature": False}
        )

        expected: int = security_settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        assert payload["exp"] - payload["iat"] == expected


    def test_verify_access_token_rejects_a_refresh_audience_even_with_access_type(
        self,
        account_id: UUID,
        jwt_token_service: JWTTokenService,
    ) -> None:
        # The audience alone is enough to refuse a token meant for refreshing.
        token: str = self._valid_access_token(
            jwt_token_service,
            account_id,
            overrides={"aud": security_settings.JWT_REFRESH_AUDIENCE},
        )
        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token(token)