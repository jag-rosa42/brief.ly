from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.domain.entities.api_key import ApiKey


class ApiKeyRepository(Protocol):
    def add(self, api_key: ApiKey) -> None: ...

    def update(self, api_key: ApiKey) -> bool:
        """
        Persist the revocation of a key that is still active.

        Returns:
            True if the stored key was updated
            False if it was already revoked (or does not exist). Nothing is
            written in this case
        """
        ...

    def find_by_id(self, api_key_id: UUID) -> ApiKey | None: ...

    def find_by_hash(self, key_hash: str) -> ApiKey | None:
        """
        Find a key by the SHA-256 hash of the full key (the gateway's lookup).
        """
        ...

    def count_active_for_account(self, account_id: UUID, now: datetime) -> int:
        """
        Count the account's keys that are neither revoked nor expired at `now`.
        """
        ...

    def list_active_for_account(self, account_id: UUID, now: datetime) -> list[ApiKey]:
        """
        The account's keys that are neither revoked nor expired at `now`,
        newest first.
        """
        ...
