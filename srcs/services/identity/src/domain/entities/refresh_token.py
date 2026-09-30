from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class RefreshToken:
    id: UUID  # the JWT's `jti`
    account_id: UUID  # the JWT's `sub`
    token_hash: str  # SHA-256 hash of the raw refresh token
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None = None
    replaced_by: UUID | None = None

    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def revoke(
        self,
        now: datetime,
        replaced_by: UUID | None = None,
    ) -> None:
        if self.is_revoked():
            return

        self.revoked_at: datetime = now
        self.replaced_by: UUID | None = replaced_by

    def was_rotated(self) -> bool:
        """
        True when this token was replaced by a new one (a rotation).

        A token revoked by logout is revoked but never rotated.
        """
        return self.replaced_by is not None
