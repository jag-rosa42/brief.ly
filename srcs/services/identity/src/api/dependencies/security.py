from typing import Annotated

from fastapi import Cookie, Depends, Header
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from src.api.dependencies.database import SessionDep, UnitOfWorkDep
from src.api.errors.exceptions import CsrfCheckFailedError
from src.application.port.password_hasher import PasswordHasher
from src.application.port.token.service import TokenService
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.application.use_cases.session.refresh_account_session import (
    RefreshAccountSession,
)
from src.application.use_cases.session.refresh_token_validator import (
    RefreshTokenValidator,
)
from src.domain.exception import InvalidTokenError
from src.domain.repositories.refresh_token_repository import RefreshTokenRepository
from src.infrastructure.config.cookie import cookie_settings
from src.infrastructure.database.repositories.sqlalchemy_refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from src.infrastructure.security.password_hasher import PwdlibPasswordHasher
from src.infrastructure.security.token.token_service import JWTTokenService


# ---------------------------------------------------------------------------
# Password Hasher
# ---------------------------------------------------------------------------
def get_password_hasher() -> PasswordHasher:
    return PwdlibPasswordHasher()


PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]


# ---------------------------------------------------------------------------
# Token Service
# ---------------------------------------------------------------------------
def get_token_service() -> TokenService:
    return JWTTokenService()


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


# ---------------------------------------------------------------------------
# Access Token
# ---------------------------------------------------------------------------
# Requires a Bearer access token in the Authorization header for protected endpoints.
# Will extracts the access token from the Authorization: Bearer <token> header.
#
# auto_error=False: without it, HTTPBearer raises its own HTTPException
# ({"detail": "Not authenticated"}), which bypasses our error format.
# It now returns None instead (missing header, or a scheme other than Bearer),
# and get_access_token turns that None into our INVALID_TOKEN error.
bearer_token_scheme = HTTPBearer(auto_error=False)

OptionalAccessTokenDep = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_token_scheme),
]


def get_access_token(
    credentials: OptionalAccessTokenDep,
) -> HTTPAuthorizationCredentials:
    """
    Require the Bearer access token. Without it there is no authenticated account.
    """
    if credentials is None:
        raise InvalidTokenError()
    return credentials


AccessTokenDep = Annotated[HTTPAuthorizationCredentials, Depends(get_access_token)]


# ---------------------------------------------------------------------------
# Refresh Token Cookie
# ---------------------------------------------------------------------------
RefreshTokenCookie = Annotated[
    str | None, Cookie(alias=cookie_settings.REFRESH_COOKIE_NAME)
]


# FastAPI forbids a default inside Annotated[..., Cookie()], so this wrapper
# holds the "= None" once: routes can use the Dep without repeating it.
def get_refresh_token_if_present(
    refresh_token: RefreshTokenCookie = None,
) -> str | None:
    return refresh_token


OptionalRefreshTokenCookieDep = Annotated[
    str | None,
    Depends(get_refresh_token_if_present),
]


def get_refresh_token(refresh_token: OptionalRefreshTokenCookieDep) -> str:
    """
    Require the refresh token cookie. Without it there is no session.
    """
    if refresh_token is None:
        raise InvalidTokenError()
    return refresh_token


RefreshTokenCookieDep = Annotated[str, Depends(get_refresh_token)]


# ---------------------------------------------------------------------------
# CSRF guard (Cross-Site Request Forgery)
# ---------------------------------------------------------------------------
# Header name and value:
#   "X-Transcendence-Client" is our own custom header, sent by the frontend on
#   every call to these endpoints. The protection comes from the header being
#   custom (it forces the preflight), not from its value: "web" only identifies
#   which client sent it. It is NOT a secret token.
#
# Defense in depth: SameSite=Strict on the cookie (see cookie.py) already blocks
# most of this. The header still holds on old browsers and against sibling
# subdomains, which count as "same-site". Never put "*" in BACKEND_CORS_ORIGINS.
#
# More details:
# - https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
# - https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS#simple_requests
ANTI_CSRF_HEADER_NAME: str = "X-Transcendence-Client"
ANTI_CSRF_HEADER_VALUE: str = "web"

CsrfRequest = Annotated[
    str | None,
    Header(alias=ANTI_CSRF_HEADER_NAME),
]


def reject_cross_site_request(client: CsrfRequest = None) -> None:
    if client != ANTI_CSRF_HEADER_VALUE:
        raise CsrfCheckFailedError()


CrossSiteGuardRequest = Depends(reject_cross_site_request)


# ---------------------------------------------------------------------------
# Refresh Token Repository
# ---------------------------------------------------------------------------
def get_refresh_token_repository(session: SessionDep) -> RefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(session)


RefreshTokenRepositoryDep = Annotated[
    RefreshTokenRepository, Depends(get_refresh_token_repository)
]


# ---------------------------------------------------------------------------
# Refresh Token Validator
# ---------------------------------------------------------------------------
def get_refresh_token_validator(
    refresh_token_repository: RefreshTokenRepositoryDep,
    token_service: TokenServiceDep,
) -> RefreshTokenValidator:
    return RefreshTokenValidator(refresh_token_repository, token_service)


RefreshTokenValidatorDep = Annotated[
    RefreshTokenValidator, Depends(get_refresh_token_validator)
]


# ---------------------------------------------------------------------------
# Create Account Session
# ---------------------------------------------------------------------------
def get_create_account_session(
    refresh_token_repository: RefreshTokenRepositoryDep,
    token_service: TokenServiceDep,
) -> CreateAccountSession:
    return CreateAccountSession(refresh_token_repository, token_service)


CreateAccountSessionDep = Annotated[
    CreateAccountSession, Depends(get_create_account_session)
]


# ---------------------------------------------------------------------------
# Refresh Account Session
# ---------------------------------------------------------------------------
def get_refresh_account_session(
    uow: UnitOfWorkDep,
    refresh_token_validator: RefreshTokenValidatorDep,
    refresh_token_repository: RefreshTokenRepositoryDep,
    create_account_session: CreateAccountSessionDep,
) -> RefreshAccountSession:
    return RefreshAccountSession(
        uow,
        refresh_token_validator,
        refresh_token_repository,
        create_account_session,
    )


RefreshAccountSessionDep = Annotated[
    RefreshAccountSession, Depends(get_refresh_account_session)
]
