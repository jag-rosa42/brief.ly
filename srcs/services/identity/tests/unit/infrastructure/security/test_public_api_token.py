from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import jwt
import pytest

from src.domain.entities.api_key import ApiKeyScope
from src.domain.exception import InvalidTokenError
from src.infrastructure.security.settings import security_settings
from src.infrastructure.security.token.token_service import JWTTokenService

PUBLIC_API: str = "transcendence:public-api"
ACCOUNT_ID = uuid4()


def decode(token: str, audience: str = PUBLIC_API) -> dict[str, Any]:
    """Decode like a receiving service would: public key, RS256, iss and aud."""
    return jwt.decode(
        token,
        security_settings.JWT_PUBLIC_KEY,
        algorithms=["RS256"],
        audience=audience,
        issuer=security_settings.JWT_ISSUER,
    )


class TestCreatePublicApiToken:
    @pytest.fixture
    def token(self, jwt_token_service: JWTTokenService) -> str:
        return jwt_token_service.create_public_api_token(
            account_id=ACCOUNT_ID,
            scopes=frozenset({ApiKeyScope.WRITE, ApiKeyScope.READ}),
        )

    def test_is_an_access_token_for_the_key_owner(self, token: str) -> None:
        claims: dict[str, Any] = decode(token)

        assert claims["sub"] == str(ACCOUNT_ID)
        assert claims["type"] == "access"
        assert claims["aud"] == PUBLIC_API
        assert claims["iss"] == security_settings.JWT_ISSUER
        assert claims["jti"]

    def test_lists_the_scopes_space_separated_and_sorted(self, token: str) -> None:
        assert decode(token)["scope"] == "read write"

    def test_lives_for_the_configured_public_api_lifetime(self, token: str) -> None:
        claims: dict[str, Any] = decode(token)

        assert claims["exp"] - claims["iat"] == 60
        assert claims["exp"] > datetime.now(UTC).timestamp()

    def test_header_carries_the_key_id(
        self, token: str, jwt_token_service: JWTTokenService
    ) -> None:
        header: dict[str, Any] = jwt.get_unverified_header(token)

        assert header["alg"] == "RS256"
        assert header["kid"] == jwt_token_service._key_id

    def test_is_refused_on_the_frontend_audience(self, token: str) -> None:
        with pytest.raises(jwt.InvalidAudienceError):
            decode(token, audience=security_settings.JWT_ACCESS_AUDIENCE)

    def test_never_opens_a_session_in_identity(
        self, token: str, jwt_token_service: JWTTokenService
    ) -> None:
        # Wrong audience: a public API token is not a browser access token.
        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token(token)

    def test_access_tokens_keep_their_own_lifetime(
        self, jwt_token_service: JWTTokenService
    ) -> None:
        # The new `lifetime` argument of _create_token must not leak into
        # the other tokens.
        claims: dict[str, Any] = decode(
            jwt_token_service.create_access_token(ACCOUNT_ID),
            audience=security_settings.JWT_ACCESS_AUDIENCE,
        )

        expected: int = security_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert claims["exp"] - claims["iat"] == expected
