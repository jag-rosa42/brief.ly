"""Test helper for services: mint real tokens and verify them for real.

FakeTokenIssuer plays Identity in a service's tests. It has its own RSA key
pair, signs tokens in Identity's format, and makes the service's app verify
them with its public key. Routes are tested through the real checks
(signature, type, audience, scopes), not by skipping them.

In a service's tests (e.g. tests/fixtures/http.py):

    from shared_auth.testing import FakeTokenIssuer

    issuer = FakeTokenIssuer()
    issuer.override_authenticator(app, service_audience="transcendence:personalization")

    client.get("/me/profile", headers=issuer.bearer(issuer.user_token(account_id)))

Only for tests: import it from shared_auth.testing, never from the service's code.
"""

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi import FastAPI
from jwcrypto.jwk import JWK

from shared_auth.api.installation import build_authenticator, get_authenticator
from shared_auth.application.authenticator import Authenticator
from shared_auth.domain.token_type import TokenType
from shared_auth.infrastructure.settings import AuthSettings

# The same defaults as the services' settings, so the tokens match them.
DEFAULT_ISSUER: str = AuthSettings.model_fields["JWT_ISSUER"].default
DEFAULT_ACCESS_AUDIENCE: str = AuthSettings.model_fields["JWT_ACCESS_AUDIENCE"].default
DEFAULT_PUBLIC_API_AUDIENCE: str = "transcendence:public-api"

ACCESS_TOKEN_LIFETIME: timedelta = timedelta(minutes=15)


class FakeTokenIssuer:
    """Signs tokens like Identity does, with a key pair made for the tests."""

    def __init__(
        self,
        *,
        issuer: str = DEFAULT_ISSUER,
        access_audience: str = DEFAULT_ACCESS_AUDIENCE,
        public_api_audience: str = DEFAULT_PUBLIC_API_AUDIENCE,
    ) -> None:
        # Generating a key takes a moment: create one issuer per test session.
        self._private_key: RSAPrivateKey = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        self.public_key_pem: str = (
            self._private_key.public_key()
            .public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
            .decode()
        )
        # Same `kid` as Identity: RFC 7638 thumbprint of the public key.
        self._key_id: str = JWK.from_pem(self.public_key_pem.encode()).thumbprint()
        self.issuer: str = issuer
        self.access_audience: str = access_audience
        self.public_api_audience: str = public_api_audience

    # -----------------------------------------------------------------------
    # Wiring the service's app
    # -----------------------------------------------------------------------

    def auth_settings(
        self, *, service_audience: str, public_api: bool = False
    ) -> AuthSettings:
        """Settings that trust this issuer, for a service with this audience."""
        return AuthSettings(
            _env_file=None,
            JWT_PUBLIC_KEY=self.public_key_pem,
            JWT_ISSUER=self.issuer,
            JWT_ACCESS_AUDIENCE=self.access_audience,
            JWT_SERVICE_AUDIENCE=service_audience,
            JWT_PUBLIC_API_AUDIENCE=self.public_api_audience if public_api else None,
        )

    def override_authenticator(
        self, app: FastAPI, *, service_audience: str, public_api: bool = False
    ) -> Authenticator:
        """Make the app verify this issuer's tokens instead of Identity's.

        Uses app.dependency_overrides, so call app.dependency_overrides.clear()
        after the test, as with any other override.
        """
        authenticator: Authenticator = build_authenticator(
            self.auth_settings(service_audience=service_audience, public_api=public_api)
        )
        app.dependency_overrides[get_authenticator] = lambda: authenticator
        return authenticator

    # -----------------------------------------------------------------------
    # Tokens
    # -----------------------------------------------------------------------

    def user_token(
        self, account_id: UUID, *, expires_in: timedelta = ACCESS_TOKEN_LIFETIME
    ) -> str:
        """A browser access token. A negative expires_in gives an expired token."""
        return self.token(
            subject=str(account_id),
            token_type=TokenType.ACCESS,
            audience=self.access_audience,
            expires_in=expires_in,
        )

    def public_api_token(self, account_id: UUID, *, scopes: Iterable[str]) -> str:
        """A public API token, as the gateway gets it for an API key."""
        return self.token(
            subject=str(account_id),
            token_type=TokenType.ACCESS,
            audience=self.public_api_audience,
            scopes=scopes,
        )

    def service_token(
        self, name: str, *, audience: str, scopes: Iterable[str] = ()
    ) -> str:
        """A service token from the service `name`, addressed to `audience`."""
        return self.token(
            subject=f"service:{name}",
            token_type=TokenType.SERVICE,
            audience=audience,
            scopes=scopes,
        )

    def token(
        self,
        *,
        subject: str,
        token_type: TokenType,
        audience: str,
        scopes: Iterable[str] = (),
        expires_in: timedelta = ACCESS_TOKEN_LIFETIME,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Any token, for unusual cases (e.g. a refresh token that must be refused)."""
        issued_at: datetime = datetime.now(UTC)
        claims: dict[str, Any] = {
            "iss": self.issuer,
            "aud": audience,
            "sub": subject,
            "jti": str(uuid4()),
            "type": token_type.value,
            "iat": issued_at,
            "exp": issued_at + expires_in,
        }
        # RFC 6749 §3.3: one space-separated string; no claim without scopes.
        scope: str = " ".join(sorted(scopes))
        if scope:
            claims["scope"] = scope
        claims.update(extra_claims or {})
        return jwt.encode(
            claims,
            key=self._private_key,
            algorithm="RS256",
            headers={"kid": self._key_id},
        )

    @staticmethod
    def bearer(token: str) -> dict[str, str]:
        """The Authorization header for a request: {"Authorization": "Bearer ..."}."""
        return {"Authorization": f"Bearer {token}"}
