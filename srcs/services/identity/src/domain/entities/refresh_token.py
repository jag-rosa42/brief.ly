from dataclasses import dataclass
from datetime import datetime
from typing import override
from uuid import UUID

from src.domain.entities.revocable import RevocableMixin


@dataclass
class RefreshToken(RevocableMixin):
    id: UUID  # the JWT's `jti`
    account_id: UUID  # the JWT's `sub`
    token_hash: str  # SHA-256 hash of the raw refresh token
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None = None
    replaced_by: UUID | None = None

    @override
    def revoke(
        self,
        now: datetime,
        replaced_by: UUID | None = None,
    ) -> None:
        if self.is_revoked():
            # Keep the first revocation: don't overwrite replaced_by. The
            # parent's revoke() checks too, but returning here is what
            # protects replaced_by, which the parent doesn't know about.
            return

        super().revoke(now)
        self.replaced_by: UUID | None = replaced_by

    def was_rotated(self) -> bool:
        """
        True when this token was replaced by a new one (a rotation).

        A token revoked by logout is revoked but never rotated.
        """
        return self.replaced_by is not None
