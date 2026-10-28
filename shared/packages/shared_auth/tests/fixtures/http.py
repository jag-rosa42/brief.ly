"""
HTTP fixtures for FastAPI integration tests.

The package has no application of its own, so the tests build a small one,
wired exactly like a service's main.py:

    register_shared_handlers(app)          # shared_errors
    install_authentication(app, settings)  # shared_auth

It has one route per dependency, with neutral paths (Routes), so the
tests send real requests and check the real error format, in the style of
shared_errors' tests.
"""

from collections.abc import Generator
from typing import Annotated, Any

import httpx2
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from shared_errors import ErrorResponse, register_shared_handlers

from shared_auth.api.dependencies import (
    CurrentForwardedUserDep,
    CurrentServiceDep,
    CurrentUserDep,
    require_public_api_scopes,
    require_service_scopes,
)
from shared_auth.api.installation import install_authentication
from shared_auth.domain.principals import ServicePrincipal, UserPrincipal
from shared_auth.infrastructure.clients.downstream_client import DownstreamClient
from shared_auth.infrastructure.settings import AuthSettings
from tests.fixtures.factory import WRITE_SCOPE

# ---------------------------------------------------------------------------
# Test app
# ---------------------------------------------------------------------------


class Routes:
    """The test app's paths, named after the dependency each one uses."""

    USER: str = "/user"
    FORWARDED_USER: str = "/forwarded-user"
    SERVICE: str = "/service"
    SCOPED_SERVICE: str = "/scoped-service"
    SCOPED_PUBLIC_USER: str = "/scoped-public-user"
    CALL_DOWNSTREAM: str = "/call-downstream"
    # On the downstream service (a MockTransport handler).
    DOWNSTREAM_RESOURCE: str = "/resources"


# A service token holding WRITE_SCOPE.
ScopedService = Annotated[ServicePrincipal, Depends(require_service_scopes(WRITE_SCOPE))]
# A public API token holding WRITE_SCOPE.
ScopedPublicUser = Annotated[
    UserPrincipal, Depends(require_public_api_scopes(WRITE_SCOPE))
]


def build_test_app(
    settings: AuthSettings,
    downstream: DownstreamClient | None = None,
) -> FastAPI:
    """One route per kind of caller, plus one that calls another service."""
    app = FastAPI()
    register_shared_handlers(app)
    install_authentication(app, settings)

    @app.get(Routes.USER)
    def user_route(user: CurrentUserDep) -> dict[str, str]:
        return {"account_id": str(user.account_id)}

    @app.get(Routes.FORWARDED_USER)
    def forwarded_user_route(user: CurrentForwardedUserDep) -> dict[str, str]:
        return {"account_id": str(user.account_id)}

    @app.get(Routes.SERVICE)
    def service_route(service: CurrentServiceDep) -> dict[str, str]:
        return {"service": service.name}

    @app.post(Routes.SCOPED_SERVICE)
    def scoped_service_route(service: ScopedService) -> dict[str, str]:
        return {"service": service.name}

    @app.post(Routes.SCOPED_PUBLIC_USER)
    def scoped_public_user_route(user: ScopedPublicUser) -> dict[str, str]:
        return {"account_id": str(user.account_id)}

    if downstream is not None:

        @app.get(Routes.CALL_DOWNSTREAM)
        def call_downstream_route(user: CurrentUserDep) -> Any:
            # Forward the user's token unchanged.
            return downstream.get_json(Routes.DOWNSTREAM_RESOURCE, token=user.token)

    return app


# ---------------------------------------------------------------------------
# FastAPI Test Client
# ---------------------------------------------------------------------------


@pytest.fixture
def client(auth_settings: AuthSettings) -> Generator[TestClient]:
    with TestClient(build_test_app(auth_settings)) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Request and response helpers
# ---------------------------------------------------------------------------


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def error_code(response: httpx2.Response) -> str:
    """The `error.code` of a shared-format error body (fails if not that format)."""
    return ErrorResponse.model_validate(response.json()).error.code
