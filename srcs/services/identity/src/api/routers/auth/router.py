"""
Authentication endpoints:

A session is made of 2 tokens:
- access token is return in the JSON body. Frontend should keep it in memory
  and sends it as "Authorization: Bearer <token>
- refresh token is set in an HttpOnly cookie (see cookie.py). Javascript never reads it

register and login only SET the cookie. refresh and logout READ it, so they
live on `cookie_session_router`, which is protected against CSRF.
"""

from fastapi import APIRouter, Response, status

from src.api.dependencies import (
    AntiCsrfGuard,
    LoginAccountDep,
    LogoutAccountDep,
    OptionalRefreshTokenCookieDep,
    RefreshAccountSessionDep,
    RefreshTokenCookieDep,
    RegisterAccountDep,
)
from src.api.routers.auth.cookie import (
    clear_refresh_token_cookie,
    set_refresh_token_cookie,
)
from src.api.schemas.authentication import (
    LoginRequest,
    RegisterRequest,
)
from src.api.schemas.session import AccessTokenResponse
from src.application.use_cases.session.account_session import AccountSession

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

# ---------------------------------------------------------------------------
# Session opening (no CSRF Guards)
# ---------------------------------------------------------------------------


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AccessTokenResponse,
)
def register(
    body: RegisterRequest,
    register_account: RegisterAccountDep,
    response: Response,
) -> AccessTokenResponse:
    session: AccountSession = register_account.execute(
        email=body.email, password=body.password.get_secret_value()
    )
    set_refresh_token_cookie(response, session.refresh_token)
    return AccessTokenResponse.from_session(session)


@router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=AccessTokenResponse,
)
def login(
    body: LoginRequest,
    login_account: LoginAccountDep,
    response: Response,
) -> AccessTokenResponse:
    session: AccountSession = login_account.execute(
        email=body.email,
        password=body.password.get_secret_value(),
    )
    set_refresh_token_cookie(response, session.refresh_token)
    return AccessTokenResponse.from_session(session)


# ---------------------------------------------------------------------------
# Cookie-based endpoints (CSRF Guards)
# ---------------------------------------------------------------------------
# These endpoints read refresh token cookie. The browser attaches that
# cookie automatically, even to requests triggered by another site, so every
# route here goes through the CSRF guard (see security.py).
#
# Router dependencies run before the endpoint's own dependencies:
# a request without the header is refused (403) before the cookie is even read.

cookie_session_router = APIRouter(dependencies=[AntiCsrfGuard])


@cookie_session_router.post(
    path="/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    refresh_token: OptionalRefreshTokenCookieDep,
    logout_account: LogoutAccountDep,
    response: Response,
) -> None:
    # Logout is idempotent: without a cookie there is nothing to revoke,
    # but the answer is still 204 and the cookie is still cleared.
    if refresh_token is not None:
        logout_account.execute(refresh_token)
    clear_refresh_token_cookie(response)


@cookie_session_router.post(
    path="/refresh",
    status_code=status.HTTP_200_OK,
    response_model=AccessTokenResponse,
)
def refresh(
    refresh_token: RefreshTokenCookieDep,
    refresh_account_session: RefreshAccountSessionDep,
    response: Response,
) -> AccessTokenResponse:
    session: AccountSession = refresh_account_session.execute(refresh_token)
    # Rotation: the old refresh token is revoked, the cookie hold the new one
    set_refresh_token_cookie(response, session.refresh_token)
    return AccessTokenResponse.from_session(session)


# Must stay at the end of the file so that all the route defines above will be included
# in the final router return by this file.
# all the route defines after will be lost
router.include_router(cookie_session_router)
