"""
JWTTokenVerifier: one test per check of the module docstring's table.

Every token comes from make_token, valid by default, with exactly one thing
broken.
"""

import hmac
import json
from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from shared_auth.domain.exceptions import InvalidTokenError, TokenExpiredError
from shared_auth.domain.token_type import TokenType
from shared_auth.domain.verified_token import VerifiedToken
from shared_auth.infrastructure.tokens.jwt_token_verifier import JWTTokenVerifier
from tests.fixtures.factory import (
    ACCESS_AUDIENCE,
    ACCOUNT_ID,
    ISSUER,
    OTHER_SERVICE_AUDIENCE,
    READ_SCOPE,
    REFRESH_AUDIENCE,
    SERVICE_NAME,
    WRITE_SCOPE,
)
from tests.fixtures.security import TokenFactory


def _expired(make_token: TokenFactory, **kwargs) -> str:
    return make_token(
        issued_ago=timedelta(minutes=20), expires_in=timedelta(minutes=15), **kwargs
    )


class TestJWTTokenVerifierAcceptsValidTokens:
    def test_returns_the_verified_claims(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        token: str = make_token(overrides={"scope": f"{READ_SCOPE} {WRITE_SCOPE}"})

        verified: VerifiedToken = verifier.verify(token)

        assert verified.subject == str(ACCOUNT_ID)
        assert verified.token_type == TokenType.ACCESS
        assert verified.audience == ACCESS_AUDIENCE
        assert verified.scopes == {READ_SCOPE, WRITE_SCOPE}
        assert verified.token_id == "token-id"
        assert verified.expires_at > datetime.now(UTC)
        assert verified.raw == token

    def test_scopes_are_empty_without_a_scope_claim(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        assert verifier.verify(make_token()).scopes == frozenset()

    def test_accepts_a_service_token(
        self, verifier: JWTTokenVerifier, service_token: TokenFactory
    ) -> None:
        verified: VerifiedToken = verifier.verify(service_token(READ_SCOPE))

        assert verified.token_type == TokenType.SERVICE
        assert verified.subject == f"service:{SERVICE_NAME}"

    def test_raw_token_is_not_in_repr(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        token: str = make_token()

        assert token not in repr(verifier.verify(token))


class TestJWTTokenVerifierRefusesBadTokens:
    # 1. kid
    def test_unknown_key_id(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(make_token(headers={"kid": "another-key"}))

    def test_missing_key_id(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(make_token(headers={}))

    @pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b.c"])
    def test_malformed(self, verifier: JWTTokenVerifier, token: str) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(token)

    # 2. signature, RS256 only
    def test_wrong_signature(
        self,
        verifier: JWTTokenVerifier,
        make_token: TokenFactory,
        other_private_key: RSAPrivateKey,
    ) -> None:
        # Same claims, same kid: only the signature is wrong.
        with pytest.raises(InvalidTokenError):
            verifier.verify(make_token(key=other_private_key))

    def test_alg_none(self, verifier: JWTTokenVerifier, make_token: TokenFactory) -> None:
        # An unsigned token: anyone could forge one if "alg" were trusted.
        token: str = make_token(key="", algorithm="none")

        with pytest.raises(InvalidTokenError):
            verifier.verify(token)

    def test_hs256_signed_with_the_public_key(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory, public_key_pem: str
    ) -> None:
        # Algorithm confusion: the public key is public, so if HS256 were
        # accepted, anyone could use it as an HMAC secret (RFC 8725 §2.1).
        # PyJWT refuses to sign HS256 with a PEM key, so the token is built by hand.
        def b64(data: bytes) -> str:
            return urlsafe_b64encode(data).rstrip(b"=").decode()

        _, payload_b64, _ = make_token().split(".")
        header = {"alg": "HS256", "typ": "JWT", "kid": verifier._key_id}
        signing_input: str = f"{b64(json.dumps(header).encode())}.{payload_b64}"
        signature: bytes = hmac.new(
            public_key_pem.encode(), signing_input.encode(), "sha256"
        ).digest()

        with pytest.raises(InvalidTokenError):
            verifier.verify(f"{signing_input}.{b64(signature)}")

    # 3. required claims
    @pytest.mark.parametrize("claim", JWTTokenVerifier.REQUIRED_CLAIMS)
    def test_missing_claim(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory, claim: str
    ) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(make_token(overrides={claim: None}))

    # 4. exp
    def test_expired(self, verifier: JWTTokenVerifier, make_token: TokenFactory) -> None:
        with pytest.raises(TokenExpiredError):
            verifier.verify(_expired(make_token))

    def test_expired_and_forged_is_invalid_not_expired(
        self,
        verifier: JWTTokenVerifier,
        make_token: TokenFactory,
        other_private_key: RSAPrivateKey,
    ) -> None:
        # The signature is checked before `exp`: a forged token must never
        # make the frontend refresh (module docstring, steps 2 and 4).
        with pytest.raises(InvalidTokenError) as error:
            verifier.verify(_expired(make_token, key=other_private_key))

        assert not isinstance(error.value, TokenExpiredError)

    # 5. iss
    def test_wrong_issuer(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(make_token(overrides={"iss": "someone-else"}))

    # 6. aud
    def test_audience_not_accepted_by_this_service(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        token: str = make_token(overrides={"aud": OTHER_SERVICE_AUDIENCE})

        with pytest.raises(InvalidTokenError):
            verifier.verify(token)

    # 7. claim types
    def test_list_audience(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        # Each token is meant for exactly one audience; a list is refused.
        token: str = make_token(overrides={"aud": [ACCESS_AUDIENCE, "other"]})

        with pytest.raises(InvalidTokenError):
            verifier.verify(token)

    def test_unknown_type(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(make_token(overrides={"type": "admin"}))

    def test_scope_of_the_wrong_type(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        with pytest.raises(InvalidTokenError):
            verifier.verify(make_token(overrides={"scope": [READ_SCOPE]}))

    # 8. type is not refresh
    def test_refresh_token_with_its_own_audience(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        token: str = make_token(overrides={"type": "refresh", "aud": REFRESH_AUDIENCE})

        with pytest.raises(InvalidTokenError):
            verifier.verify(token)

    def test_refresh_token_even_with_an_accepted_audience(
        self, verifier: JWTTokenVerifier, make_token: TokenFactory
    ) -> None:
        # Defence in depth: refused on its type alone.
        token: str = make_token(overrides={"type": "refresh"})

        with pytest.raises(InvalidTokenError):
            verifier.verify(token)


class TestJWTTokenVerifierConfiguration:
    def test_exposes_its_audiences(self, verifier: JWTTokenVerifier) -> None:
        assert ACCESS_AUDIENCE in verifier.audiences

    def test_requires_at_least_one_audience(self, public_key_pem: str) -> None:
        with pytest.raises(ValueError):
            JWTTokenVerifier(public_key_pem=public_key_pem, issuer=ISSUER, audiences=[])

    def test_refuses_an_invalid_public_key(self) -> None:
        with pytest.raises(ValueError):
            JWTTokenVerifier(
                public_key_pem="not a key", issuer=ISSUER, audiences=[ACCESS_AUDIENCE]
            )

    def test_refuses_a_non_rsa_public_key(self) -> None:
        ec_pem: str = (
            ec.generate_private_key(ec.SECP256R1())
            .public_key()
            .public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
            .decode()
        )

        with pytest.raises(ValueError, match="RSA"):
            JWTTokenVerifier(
                public_key_pem=ec_pem, issuer=ISSUER, audiences=[ACCESS_AUDIENCE]
            )

    def test_refuses_a_private_key(self, private_key: RSAPrivateKey) -> None:
        # Only the issuer may hold the private key: a service given
        # one by mistake must not start.
        private_pem: str = private_key.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
        ).decode()

        with pytest.raises(ValueError, match="not a private key"):
            JWTTokenVerifier(
                public_key_pem=private_pem, issuer=ISSUER, audiences=[ACCESS_AUDIENCE]
            )
