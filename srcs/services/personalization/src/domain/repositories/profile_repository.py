from typing import Protocol
from uuid import UUID

from src.domain.entities.profile import Profile


class ProfileRepository(Protocol):
    def upsert(self, profile: Profile) -> bool: ...

    def find_by_id(self, account_id: UUID) -> Profile | None: ...

    def find_by_id_for_update(self, account_id: UUID) -> Profile | None:
        """Like find_by_id, but locks the profile row until the transaction ends."""
        ...
