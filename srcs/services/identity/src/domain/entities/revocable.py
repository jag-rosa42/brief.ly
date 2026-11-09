from datetime import datetime


class RevocableMixin:
    """Expiry and revocation, shared by the credentials Identity hands out.

    Refresh tokens and API keys both expire at a fixed date and can be revoked
    before it. The rules are the same for both, so they're written once here:

    - expired from `expires_at` included;
    - active means neither revoked nor expired;
    - revoking twice keeps the first revocation date.

    A mixin: a base class that only adds methods. It has no dataclass fields
    of its own: each entity declares `expires_at` and `revoked_at` itself, so
    the order of its fields (and of its constructor's arguments) doesn't
    change.
    """

    # Declared for the type checker only: the entity's dataclass owns them.
    expires_at: datetime
    revoked_at: datetime | None

    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def is_active(self, now: datetime) -> bool:
        """True when the credential can still be used: neither revoked nor expired."""
        return not self.is_revoked() and not self.is_expired(now)

    def revoke(self, now: datetime) -> None:
        if self.is_revoked():
            return
        self.revoked_at: datetime = now
