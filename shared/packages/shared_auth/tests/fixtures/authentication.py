"""
The objects a service builds at startup: settings, verifier, authenticator.
"""

import pytest

from shared_auth.api.installation import build_authenticator
from shared_auth.application.authenticator import Authenticator
from shared_auth.infrastructure.settings import AuthSettings
from shared_auth.infrastructure.tokens.jwt_token_verifier import JWTTokenVerifier
from tests.fixtures.factory import (
    ACCESS_AUDIENCE,
    ISSUER,
    PUBLIC_API_AUDIENCE,
    SERVICE_AUDIENCE,
)


@pytest.fixture
def auth_settings(public_key_pem: str) -> AuthSettings:
    """Settings of a service that also serves a public API.

    Every value is given explicitly, so the tests don't depend on the
    defaults (which are the project's real names).
    _env_file=None: never read a real .env file during the tests.
    """
    return AuthSettings(
        _env_file=None,
        JWT_PUBLIC_KEY=public_key_pem,
        JWT_ISSUER=ISSUER,
        JWT_ACCESS_AUDIENCE=ACCESS_AUDIENCE,
        JWT_SERVICE_AUDIENCE=SERVICE_AUDIENCE,
        JWT_PUBLIC_API_AUDIENCE=PUBLIC_API_AUDIENCE,
    )


@pytest.fixture
def auth_settings_without_public_api(auth_settings: AuthSettings) -> AuthSettings:
    """Settings of a service with no public API."""
    return auth_settings.model_copy(update={"JWT_PUBLIC_API_AUDIENCE": None})


@pytest.fixture
def verifier(auth_settings: AuthSettings) -> JWTTokenVerifier:
    return JWTTokenVerifier(
        public_key_pem=auth_settings.JWT_PUBLIC_KEY,
        issuer=auth_settings.JWT_ISSUER,
        audiences=auth_settings.accepted_audiences,
    )


@pytest.fixture
def authenticator(auth_settings: AuthSettings) -> Authenticator:
    return build_authenticator(auth_settings)
