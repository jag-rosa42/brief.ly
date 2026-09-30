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
    token_hash: str
    expires_at: datetime


@dataclass(frozen=True)
class CreatedToken:
    token: str
    id: UUID
    expires_at: datetime
