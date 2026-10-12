from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from src.api.dependencies.database import SessionDep, UnitOfWorkDep
from src.application.port.password_hasher import PasswordHasher
from src.application.port.token.service import TokenService
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.application.use_cases.session.refresh_account_session import (
    RefreshAccountSession,
)
from src.application.use_cases.session.refresh_token_validator import (
    RefreshTokenValidator,
)
from src.domain.repositories.refresh_token_repository import RefreshTokenRepository
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
bearer_token_scheme = HTTPBearer()

AccessTokenDep = Annotated[HTTPAuthorizationCredentials, Depends(bearer_token_scheme)]


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
