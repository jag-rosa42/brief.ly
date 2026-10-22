from dataclasses import dataclass, field
from datetime import datetime

from shared_auth.domain.token_type import TokenType


@dataclass(frozen=True)
class VerifiedToken:
    """A token whose signature and claims have been checked."""

    subject: str
    token_type: TokenType
    audience: str
    scopes: frozenset[str]
    token_id: str
    expires_at: datetime
    # The original token, kept so it can be forwarded unchanged to another
    # service. Hidden from repr() so it never ends up in a log line.
    raw: str = field(repr=False)
