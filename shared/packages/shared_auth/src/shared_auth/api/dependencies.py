"""FastAPI dependencies: what runs on each request, to identify the caller.

Usage example on routes:

    # frontend route: a browser user
        def get_my_profile(user: CurrentUserDep): ...

    # internal /me route: a user token forwarded by another service
    # (browser access token or public API token)
        def get_profile_for_briefing(user: CurrentForwardedUserDep): ...

    # public route: a public API token holding the scope
        Writer = Depends(require_public_api_scopes("write"))
        def update_profile(user: Annotated[UserPrincipal, Writer]): ...

    # internal route: a service token holding the scope
        SummaryWriter = Depends(require_service_scopes("summaries:write"))
        def put_summary(service: Annotated[ServicePrincipal, SummaryWriter]): ...

The authenticator itself is built once at startup (installation.py).
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared_auth.api.installation import get_authenticator
from shared_auth.application.authenticator import Authenticator
from shared_auth.domain.exceptions import InvalidTokenError
from shared_auth.domain.principals import ServicePrincipal, UserPrincipal
from shared_auth.domain.scopes import ensure_scopes

# ---------------------------------------------------------------------------
# Authenticator Dep
# ---------------------------------------------------------------------------

AuthenticatorDep = Annotated[Authenticator, Depends(get_authenticator)]

# ---------------------------------------------------------------------------
# Bearer token
# ---------------------------------------------------------------------------
# auto_error=False: FastAPI's own error would be {"detail": "Not authenticated"};
# raising our own error keeps the shared error format.
bearer_scheme = HTTPBearer(auto_error=False)


CredentialsDep = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def get_bearer_token(credentials: CredentialsDep) -> str:
    if credentials is None:
        raise InvalidTokenError()
    return credentials.credentials


BearerTokenDep = Annotated[
    str,
    Depends(get_bearer_token),
]


# ---------------------------------------------------------------------------
# Callers
# ---------------------------------------------------------------------------
def get_current_user(
    token: BearerTokenDep,
    authenticator: AuthenticatorDep,
) -> UserPrincipal:
    return authenticator.user(token)


CurrentUserDep = Annotated[
    UserPrincipal,
    Depends(get_current_user),
]


def get_current_forwarded_user(
    token: BearerTokenDep,
    authenticator: AuthenticatorDep,
) -> UserPrincipal:
    return authenticator.forwarded_user(token)


CurrentForwardedUserDep = Annotated[
    UserPrincipal,
    Depends(get_current_forwarded_user),
]


def get_current_service(
    token: BearerTokenDep,
    authenticator: AuthenticatorDep,
) -> ServicePrincipal:
    return authenticator.service(token)


CurrentServiceDep = Annotated[
    ServicePrincipal,
    Depends(get_current_service),
]


# ---------------------------------------------------------------------------
# Scopes
# ---------------------------------------------------------------------------
# Each factory returns a dependency, used as:
#     caller: Annotated[ServicePrincipal, Depends(require_service_scopes("x:read"))]


def require_service_scopes(*scopes: str) -> Callable[..., ServicePrincipal]:
    """A service token holding every given scope."""

    def dependency(service: CurrentServiceDep) -> ServicePrincipal:
        ensure_scopes(service, scopes)
        return service

    return dependency


def require_public_api_scopes(*scopes: str) -> Callable[..., UserPrincipal]:
    """A public API token (ADR-0009) holding every given scope."""

    def dependency(
        token: BearerTokenDep, authenticator: AuthenticatorDep
    ) -> UserPrincipal:
        user: UserPrincipal = authenticator.public_api_user(token)
        ensure_scopes(user, scopes)
        return user

    return dependency
