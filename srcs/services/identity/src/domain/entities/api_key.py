from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from src.domain.entities.revocable import RevocableMixin

# ---------------------------------------------------------------------------
# Rules of the Public API keys (ADR-0009)
# ---------------------------------------------------------------------------
# Fixed by decision, not configurable: a key always lives 48 hours, and an
# account has at most 5 active keys (not revoked and not expired).
API_KEY_LIFETIME: timedelta = timedelta(hours=48)
MAX_ACTIVE_API_KEYS_PER_ACCOUNT: int = 5


class ApiKeyScope(StrEnum):
    """What a key may do on the public API."""
    READ = "read"
    WRITE = "write"


@dataclass
class ApiKey(RevocableMixin):
    """A key a third-party program sends as `X-API-Key` on /public/v1 routes.

    The key itself is never stored: only its SHA-256 hash, to find it again,
    and its first characters (`prefix`), so the user can recognise it in
    the list. The full key is shown once, when it is created.

    Expiry and revocation come from RevocableMixin, shared with refresh
    tokens.
    """
    id: UUID
    account_id: UUID  # the owner: public requests act on this account's data
    name: str  # a label chosen by the user, e.g. "my script"
    prefix: str  # e.g. "tr_8f3k"
    key_hash: str  # SHA-256 hash of the full key
    scopes: frozenset[ApiKeyScope]
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
