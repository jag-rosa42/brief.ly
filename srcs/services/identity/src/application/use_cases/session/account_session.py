from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AccountSession:
    access_token: str
    refresh_token: str
    refresh_token_id: UUID
    token_type: str = "Bearer"
