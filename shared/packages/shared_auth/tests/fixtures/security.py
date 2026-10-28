"""
An RSA key pair standing in for the token issuer's, and factories that mint
tokens in the format the verifier expects: valid by default, so each test
breaks one thing.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from jwcrypto.jwk import JWK

from tests.fixtures.factory import (
    ACCESS_AUDIENCE,
    ACCOUNT_ID,
    ISSUER,
    SERVICE_AUDIENCE,
    SERVICE_NAME,
)

TokenFactory = Callable[..., str]


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------
# Generating an RSA key is slow: one pair for the whole test session.


@pytest.fixture(scope="session")
def private_key() -> RSAPrivateKey:
    """The issuer's private key: only the tests (playing the issuer) use it."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def public_key_pem(private_key: RSAPrivateKey) -> str:
    """What a service receives to verify tokens."""
    return (
        private_key.public_key()
        .public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )


@pytest.fixture(scope="session")
def other_private_key() -> RSAPrivateKey:
    """A key that is NOT the issuer's: tokens signed with it must be refused."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------


@pytest.fixture
def make_token(private_key: RSAPrivateKey, public_key_pem: str) -> TokenFactory:
    """Mint a token. Default: a valid browser access token.

    overrides:  replace or add claims (e.g. {"aud": "..."}); None removes one
    headers:    replace the default header (which carries the right kid)
    key:        sign with another private key
    algorithm:  sign with another algorithm (e.g. "none")
    expires_in, issued_ago: control `iat` and `exp`
    """
    # The key ID the verifier expects: RFC 7638 thumbprint of the public key.
    key_id: str = JWK.from_pem(public_key_pem.encode()).thumbprint()

    def _make(
        *,
        overrides: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        key: Any = None,
        algorithm: str = "RS256",
        expires_in: timedelta = timedelta(minutes=15),
        issued_ago: timedelta = timedelta(0),
    ) -> str:
        issued_at: datetime = datetime.now(UTC) - issued_ago
        payload: dict[str, Any] = {
            "iss": ISSUER,
            "aud": ACCESS_AUDIENCE,
            "sub": str(ACCOUNT_ID),
            "jti": "token-id",
            "type": "access",
            "iat": issued_at,
            "exp": issued_at + expires_in,
        }
        for claim, value in (overrides or {}).items():
            if value is None:
                payload.pop(claim, None)
            else:
                payload[claim] = value

        return jwt.encode(
            payload,
            key=key if key is not None else private_key,
            algorithm=algorithm,
            headers=headers if headers is not None else {"kid": key_id},
        )

    return _make


@pytest.fixture
def service_token(make_token: TokenFactory) -> TokenFactory:
    """Mint a service token addressed to this service, with the given scopes.

    service_token(READ_SCOPE)                -> valid service token
    service_token(overrides={"aud": "..."})  -> break one claim
    """

    def _make(scope: str = "", **kwargs: Any) -> str:
        overrides: dict[str, Any] = {
            "type": "service",
            "aud": SERVICE_AUDIENCE,
            "sub": f"service:{SERVICE_NAME}",
            "scope": scope,
            **kwargs.pop("overrides", {}),
        }
        return make_token(overrides=overrides, **kwargs)

    return _make
