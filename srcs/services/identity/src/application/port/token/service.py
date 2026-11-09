from typing import Protocol
from uuid import UUID

from src.application.port.token.types import (
    AccessTokenClaims,
    CreatedRefreshToken,
    RefreshTokenClaims,
)


class TokenService(Protocol):
    def create_access_token(self, account_id: UUID) -> str: ...

    # These methods are called "verify" rather than "decode" because they do more
    # than decode the JWT: they validate its signature, required claims,
    # expiration, and expected token type before returning the claims.
    def verify_access_token(self, token: str) -> AccessTokenClaims: ...
    def verify_refresh_token(self, token: str) -> RefreshTokenClaims: ...

    def create_refresh_token(self, account_id: UUID) -> CreatedRefreshToken: ...
