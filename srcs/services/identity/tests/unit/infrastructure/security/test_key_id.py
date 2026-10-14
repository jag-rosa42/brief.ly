import base64

import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from src.infrastructure.security.token.token_service import JWTTokenService

# Example key and expected thumbprint from RFC 7638, section 3.1.
RFC_7638_N: str = (
    "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxu"
    "hDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN"
    "5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5"
    "hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBni"
    "Iqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw"
)   
RFC_7638_E: str = "AQAB"
RFC_7638_THUMBPRINT: str = "NzbLsXh8uDCcd-6MNwXF4W_7noWXFZAfHkxZsRGC9Xs"


def _base64url_to_int(value: str) -> int:
    padded: str = value + "=" * (-len(value) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(padded), "big")


def _to_pem(public_key) -> str:
    return public_key.public_bytes(
        Encoding.PEM, PublicFormat.SubjectPublicKeyInfo
    ).decode()


def _new_rsa_pem() -> str:
    return _to_pem(
        rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
    )


class TestComputeKeyId:
    def test_matches_the_rfc_7638_example(self) -> None:
        public_key = rsa.RSAPublicNumbers(
            e=_base64url_to_int(RFC_7638_E),
            n=_base64url_to_int(RFC_7638_N),
        ).public_key()

        assert JWTTokenService._compute_key_id(_to_pem(public_key)) == RFC_7638_THUMBPRINT

    def test_is_stable_for_the_same_key(self) -> None:
        pem: str = _new_rsa_pem()

        assert JWTTokenService._compute_key_id(pem) == JWTTokenService._compute_key_id(
            pem
        )

    def test_differs_between_keys(self) -> None:
        assert JWTTokenService._compute_key_id(
            _new_rsa_pem()
        ) != JWTTokenService._compute_key_id(_new_rsa_pem())

    def test_rejects_a_non_rsa_key(self) -> None:
        ec_pem: str = _to_pem(ec.generate_private_key(ec.SECP256R1()).public_key())

        with pytest.raises(ValueError):
            JWTTokenService._compute_key_id(ec_pem)

    def test_rejects_an_invalid_pem(self) -> None:
        # Checked locally: jwcrypto raises ValueError for a non-PEM input.
        with pytest.raises(ValueError):
            JWTTokenService._compute_key_id("not-a-pem")