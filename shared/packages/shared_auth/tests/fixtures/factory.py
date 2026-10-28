"""
Constants and plain builders shared by the tests (no pytest fixtures here).

Every name is a made-up example, not a real service of the project: the
package only compares these strings, it never gives them a meaning.
"""

from uuid import UUID, uuid4

import httpx2

from shared_auth.domain.principals import ServicePrincipal, UserPrincipal

# ---------------------------------------------------------------------------
# Token claims
# ---------------------------------------------------------------------------

ISSUER: str = "example:issuer"
# Browser access tokens.
ACCESS_AUDIENCE: str = "example:api"
# Service tokens addressed to the service under test.
SERVICE_AUDIENCE: str = "example:this-service"
# Public API tokens.
PUBLIC_API_AUDIENCE: str = "example:public-api"
# Refresh tokens: only the issuer accepts them, never a service.
REFRESH_AUDIENCE: str = "example:refresh"
# Tokens meant for another service: this one must refuse them.
OTHER_SERVICE_AUDIENCE: str = "example:other-service"

ACCOUNT_ID: UUID = uuid4()
# The service calling us, in service tokens (`sub` is "service:<name>").
SERVICE_NAME: str = "caller-service"

READ_SCOPE: str = "example:read"
WRITE_SCOPE: str = "example:write"


# ---------------------------------------------------------------------------
# Principals
# ---------------------------------------------------------------------------


def build_user_principal(*scopes: str) -> UserPrincipal:
    return UserPrincipal(account_id=ACCOUNT_ID, scopes=frozenset(scopes), token="t")


def build_service_principal(*scopes: str) -> ServicePrincipal:
    return ServicePrincipal(name=SERVICE_NAME, scopes=frozenset(scopes), token="t")


# ---------------------------------------------------------------------------
# Downstream answers
# ---------------------------------------------------------------------------


def build_error_response(status_code: int, code: str) -> httpx2.Response:
    """An error answer in the shared format, as another service would send it."""
    return httpx2.Response(
        status_code,
        json={"error": {"code": code, "message": "downstream message"}},
    )
