"""
Authentication fixtures for FastAPI tests.

``token_issuer`` plays Identity: it signs real service tokens with a test
key, and the app verifies them through shared_auth's real checks
(signature, type, audience, scopes).

``authenticate`` is autouse: every test's app trusts the test issuer. The
test clients send ``service_headers`` by default, a token with every scope,
so tests about something else don't have to think about tokens. The token
checks themselves are tested in tests/unit/api/test_service_auth.py.
"""

from collections.abc import Generator

import pytest
from shared_auth.api.installation import get_authenticator
from shared_auth.testing import FakeTokenIssuer

from src.main import app

# Same value as JWT_SERVICE_AUDIENCE in the service's .env.
SERVICE_AUDIENCE: str = "transcendence:content-management"
ALL_SCOPES: tuple[str, ...] = ("topics:read", "articles:read", "summaries:write")


@pytest.fixture(scope="session")  # generating the key is slow: once per session
def token_issuer() -> FakeTokenIssuer:
    return FakeTokenIssuer()


@pytest.fixture(autouse=True)
def authenticate(token_issuer: FakeTokenIssuer) -> Generator[None]:
    token_issuer.override_authenticator(app, service_audience=SERVICE_AUDIENCE)
    yield
    app.dependency_overrides.pop(get_authenticator, None)


@pytest.fixture
def service_headers(token_issuer: FakeTokenIssuer) -> dict[str, str]:
    """The Authorization header of a service token with every scope."""
    token = token_issuer.service_token(
        "ai-processing", audience=SERVICE_AUDIENCE, scopes=ALL_SCOPES
    )
    return token_issuer.bearer(token)
