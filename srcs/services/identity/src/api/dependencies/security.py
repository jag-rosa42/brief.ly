from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from src.application.port.password_hasher import PasswordHasher
from src.application.port.token.service import TokenService
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
bearer_token_scheme = HTTPBearer()

AccessTokenDep = Annotated[HTTPAuthorizationCredentials, Depends(bearer_token_scheme)]
