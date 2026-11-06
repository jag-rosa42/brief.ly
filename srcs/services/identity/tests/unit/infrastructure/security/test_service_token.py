from datetime import UTC, datetime
from typing import Any

import jwt
import pytest

from src.application.port.token.types import CreatedServiceToken
from src.domain.exception import InvalidTokenError
from src.infrastructure.security.settings import security_settings
from src.infrastructure.security.token.token_service import JWTTokenService

CONTENT_MANAGEMENT: str = "transcendence:content-management"


def decode(token: str, audience: str = CONTENT_MANAGEMENT) -> dict[str, Any]:
    """Decode like a receiving service would: public key, RS256, iss and aud."""
    return jwt.decode(
        token,
        security_settings.JWT_PUBLIC_KEY,
        algorithms=["RS256"],
        audience=audience,
        issuer=security_settings.JWT_ISSUER,
    )


class TestCreateServiceToken:
    @pytest.fixture
    def created(self, jwt_token_service: JWTTokenService) -> CreatedServiceToken:
        return jwt_token_service.create_service_token(
            client_id="personalization",
            audience=CONTENT_MANAGEMENT,
            scopes=frozenset({"topics:read", "articles:read"}),
        )

    def test_carries_the_service_claims(self, created: CreatedServiceToken) -> None:
        claims: dict[str, Any] = decode(created.token)

        assert claims["sub"] == "service:personalization"
        assert claims["type"] == "service"
        assert claims["aud"] == CONTENT_MANAGEMENT
        assert claims["iss"] == security_settings.JWT_ISSUER
        assert claims["jti"]

    def test_lists_the_scopes_space_separated_and_sorted(
        self, created: CreatedServiceToken
    ) -> None:
        assert decode(created.token)["scope"] == "articles:read topics:read"

    def test_lives_for_the_configured_service_lifetime(
        self, created: CreatedServiceToken
    ) -> None:
        claims: dict[str, Any] = decode(created.token)
        expected_seconds: int = security_settings.SERVICE_TOKEN_EXPIRE_MINUTES * 60

        assert created.expires_in == expected_seconds
        assert claims["exp"] - claims["iat"] == expected_seconds
        assert claims["exp"] > datetime.now(UTC).timestamp()

    def test_header_carries_the_key_id(
        self, created: CreatedServiceToken, jwt_token_service: JWTTokenService
    ) -> None:
        header: dict[str, Any] = jwt.get_unverified_header(created.token)

        assert header["alg"] == "RS256"
        assert header["kid"] == jwt_token_service._key_id

    def test_is_refused_by_another_audience(self, created: CreatedServiceToken) -> None:
        with pytest.raises(jwt.InvalidAudienceError):
            decode(created.token, audience="transcendence:morning-briefing")

    def test_is_refused_as_an_access_token(
        self, created: CreatedServiceToken, jwt_token_service: JWTTokenService
    ) -> None:
        # Wrong audience and wrong type: a service token never opens a
        # session in Identity.
        with pytest.raises(InvalidTokenError):
            jwt_token_service.verify_access_token(created.token)
