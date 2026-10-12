from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(Protocol):
    def add(self, refresh_token: RefreshToken) -> None: ...

    def update(self, refresh_token: RefreshToken) -> bool: ...
    """
    Persist the revocation of a refresh token that is still active.

    Returns:
        True if the stored token was updated
        False if it was already revoked (or does not exist). Nothing is written
        in this case
    """

    def find_by_id(self, refresh_token_id: UUID) -> RefreshToken | None: ...

    def find_by_id_for_update(self, refresh_token_id: UUID) -> RefreshToken | None: ...
    """
    Load a refresh token and lock it until the transaction ends

    A concurrent caller locking the same token waits until this transaction commits
    or rolls back, then read the committed state
    """

    def revoke_all_for_account(self, account_id: UUID, now: datetime) -> None: ...
