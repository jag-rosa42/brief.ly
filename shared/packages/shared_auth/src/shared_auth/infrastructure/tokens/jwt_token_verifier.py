"""Local verification of the JWTs issued by Identity (ADR-0007).

Every service checks tokens itself, with Identity's public key: no call to
Identity per request. Identity signs with its private key; a public key can
check a signature but cannot create one, so a service can never forge a token.

Checks, in this order (the cheapest and least trusted first):

    1. header `kid` matches our key       else InvalidTokenError  (401 INVALID_TOKEN)
    2. signature valid with RS256 only    else InvalidTokenError
    3. all required claims present        else InvalidTokenError
    4. `exp` not passed                   else TokenExpiredError  (401 TOKEN_EXPIRED)
    5. `iss` is Identity                  else InvalidTokenError
    6. `aud` is one we accept             else InvalidTokenError
    7. claims have the expected types     else InvalidTokenError
    8. `type` is not "refresh"            else InvalidTokenError

Steps 2 to 6 are done by PyJWT in one call (jwt.decode), in this order
(PyJWT 2.15). So TOKEN_EXPIRED is only returned for a token that is authentic
and complete: a forged or incomplete expired token gets INVALID_TOKEN.

Standards:
    - RFC 7519, JSON Web Token (JWT): the claims iss, aud, sub, jti, iat, exp
      https://datatracker.ietf.org/doc/html/rfc7519#section-4.1
    - RFC 7515 §4.1.4, the `kid` header parameter
      https://datatracker.ietf.org/doc/html/rfc7515#section-4.1.4
    - RFC 7518 §3.3, RS256 (RSASSA-PKCS1-v1_5 with SHA-256)
      https://datatracker.ietf.org/doc/html/rfc7518#section-3.3
    - RFC 7638, JWK thumbprint (how the `kid` is computed)
      https://datatracker.ietf.org/doc/html/rfc7638
    - RFC 8725, JWT best current practices: pin the algorithm, check iss/aud,
      tell token types apart
      https://datatracker.ietf.org/doc/html/rfc8725
    - RFC 9068, JWT profile for OAuth 2.0 access tokens
      https://datatracker.ietf.org/doc/html/rfc9068

Library documentation:
    - PyJWT, jwt.decode() and its options
      https://pyjwt.readthedocs.io/en/stable/api.html#jwt.decode
    - jwcrypto, JWK.thumbprint()
      https://jwcrypto.readthedocs.io/en/latest/jwk.html
"""
import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, ClassVar

import jwt
from jwcrypto.jwk import JWK

from shared_auth.domain.exceptions import InvalidTokenError, TokenExpiredError
from shared_auth.domain.token_type import TokenType
from shared_auth.domain.verified_token import VerifiedToken
from shared_auth.infrastructure.tokens.token_claims import TokenClaims

logger: logging.Logger = logging.getLogger(__name__)


class JWTTokenVerifier:
    """Verify JWTs issued by Identity, locally, with Identity's public key.

    Build it once at startup: the constructor parses the key, so a missing or
    invalid key fails immediately instead of on the first request.
    """

    # Pinned: the algorithm written in the token header is never trusted.
    # Otherwise an attacker could send `alg: none` (no signature) or `HS256`
    # with our public key used as an HMAC secret (RFC 8725 §2.1, §3.1).
    ALGORITHM: ClassVar[str] = "RS256"
    # Identity always sets these (ADR-0007). A token missing one is refused,
    # even if its signature is valid.
    REQUIRED_CLAIMS: ClassVar[tuple[str, ...]] = (
        "iss",
        "aud",
        "jti",
        "sub",
        "type",
        "iat",
        "exp",
    )

    def __init__(
        self,
        *,
        public_key_pem: str,
        issuer: str,
        audiences: Iterable[str],
    ) -> None:
        """Parse the key and store what every token must match.

        Args:
            public_key_pem: Identity's RSA public key, in PEM format (the
                `jwt_public_key` secret).
            issuer: The only accepted `iss`, e.g. "transcendence:identity".
            audiences: The `aud` values this service accepts, e.g. the access
                token audience plus its own service audience
                (AuthSettings.accepted_audiences).

        Raises:
            ValueError: No audience given, or the key is not an RSA public key.
        """
        # frozenset to have an Immutable set and without duplicates.
        self._audiences: frozenset[str] = frozenset(audiences)
        if not self._audiences:
            raise ValueError("A TokenVerifier needs at least one accepted audience claim")
        self._key_id: str = self._compute_key_id(public_key_pem)
        self._public_key: str = public_key_pem
        self._issuer: str = issuer

    @property
    def audiences(self) -> frozenset[str]:
        return self._audiences

    def verify(self, token: str) -> VerifiedToken:
        """Check a raw token and return what the rest of the code needs from it.

        Args:
            token: The string after "Bearer " in the Authorization header.

        Returns:
            A VerifiedToken. It only says the token is authentic and meant for
            this service; whether the caller may use a given route (user or
            service, scopes) is decided later, by the Authenticator.

        Raises:
            TokenExpiredError: The signature is valid but `exp` has passed
                (401 TOKEN_EXPIRED: the frontend refreshes and retries).
            InvalidTokenError: Anything else is wrong (401 INVALID_TOKEN). The
                reason is not given to the caller, so an attacker learns
                nothing about which check failed.
        """
        claims: TokenClaims = self._decode(token)

        return VerifiedToken(
            subject=claims.subject,
            token_type=claims.token_type,
            audience=claims.audience,
            scopes=frozenset(claims.scope.split()),
            token_id=claims.token_id,
            expires_at=datetime.fromtimestamp(claims.expires_at, tz=UTC),
            raw=token,
        )

    @staticmethod
    def _compute_key_id(public_key_pem: str) -> str:
        """Return the key ID (`kid`) to put in every token header.

        The `kid` is the RFC 7638 thumbprint of the public key (SHA-256,
        base64url), so it never has to be configured by hand and it changes
        whenever the key changes.

        Raises:
            ValueError: If the PEM is not a valid RSA public key or is a private key.
            This runs at startup, so a bad key fails immediately rather than on a request.
        """
        public_jwk: JWK = JWK.from_pem(public_key_pem.encode())
        if public_jwk.has_private:
            raise ValueError("JWT_PUBLIC_KEY must be a public key, not a private key")
        if public_jwk.get("kty") != "RSA":
            raise ValueError("JWT_PUBLIC_KEY must be an RSA public key")
        return public_jwk.thumbprint()

    def _decode(self, token: str) -> TokenClaims:
        """Run every check and return the typed claims.

        Raises:
            TokenExpiredError: `exp` has passed.
            InvalidTokenError: Any other check failed.
        """
        self._check_key_id(token)
        payload: dict[str, Any] = self._decode_payload(token)
        claims: TokenClaims = TokenClaims.from_dict(payload)
        self._reject_refresh_token(claims)
        return claims

    def _check_key_id(self, token: str) -> None:
        """Refuse a token signed with a key other than Identity's current one.

        Raises:
            InvalidTokenError: The header cannot be read, or its `kid` differs.
        """
        # The header is read before the signature is checked, so it is
        # only used to select the key: a token signed by a key we don't
        # know is refused immediately.
        try:
            header: dict[str, Any] = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError() from exc
        if header.get("kid") != self._key_id:
            logger.debug("Unknown token key id")
            raise InvalidTokenError()

    def _decode_payload(self, token: str) -> dict[str, Any]:
        """Check the signature and the standard claims, then return the payload.

        PyJWT checks, in one call: the signature (RS256 only), that every
        REQUIRED_CLAIMS is present, `exp`, `iss`, and `aud` (one of ours). No
        leeway: the services and Identity run on the same host clock.

        Raises:
            TokenExpiredError: `exp` has passed.
            InvalidTokenError: Any other check failed.
        """
        try:
            return jwt.decode(
                jwt=token,
                key=self._public_key,
                algorithms=[self.ALGORITHM],
                audience=self._audiences,
                issuer=self._issuer,
                options={"require": list(self.REQUIRED_CLAIMS)},
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError() from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError() from exc

    @staticmethod
    def _reject_refresh_token(claims: TokenClaims) -> None:
        """Refuse refresh tokens, even with a valid signature.

        Raises:
            InvalidTokenError: The token's `type` is "refresh".
        """
        # Refresh tokens are only for identity; no service may accept one.
        if claims.token_type == TokenType.REFRESH:
            logger.debug("Refresh token presented to a service")
            raise InvalidTokenError()
