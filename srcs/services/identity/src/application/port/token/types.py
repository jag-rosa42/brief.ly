from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AccessTokenPayload:
    account_id: UUID
    expires_at: datetime
