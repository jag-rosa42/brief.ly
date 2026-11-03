"""
Authentication fixtures for FastAPI integration tests.

``token_issuer`` plays Identity: it signs real tokens with a test key, and
the app verifies them through shared_auth's real checks.
"""

from collections.abc import Callable
from uuid import UUID

import pytest
from shared_auth.testing import FakeTokenIssuer

# Same value as JWT_SERVICE_AUDIENCE in the service's .env.
SERVICE_AUDIENCE: str = "transcendence:personalization"
AuthHeaders = Callable[[UUID], dict[str, str]]


@pytest.fixture(scope="session")  # generating the key is slow: once per session
def token_issuer() -> FakeTokenIssuer:
    return FakeTokenIssuer()


@pytest.fixture
def auth_headers(token_issuer: FakeTokenIssuer) -> AuthHeaders:
    """Build the Authorization header of a valid access token for an account."""

    def build(account_id: UUID) -> dict[str, str]:
        return token_issuer.bearer(token_issuer.user_token(account_id))

    return build
