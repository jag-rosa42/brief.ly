from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AccessTokenClaims:
    account_id: UUID
    expires_at: datetime


@dataclass(frozen=True)
class RefreshTokenClaims:
    id: UUID
    account_id: UUID
    expires_at: datetime


@dataclass(frozen=True)
class CreatedRefreshToken:
    id: UUID
    token: str
    expires_at: datetime


@dataclass(frozen=True)
class CreatedToken:
    token: str
    id: UUID
    expires_at: datetime

@dataclass(frozen=True)
class CreatedServiceToken:
    token: str
    # Lifetime in seconds: the token response gives it as `expires_in`
    # (RFC 6749 §5.1), so the client knows when to renew.
    expires_in: int
