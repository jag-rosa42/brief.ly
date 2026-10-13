from typing import Protocol
from uuid import UUID

from src.domain.entities.profile import Profile


class ProfileRepository(Protocol):
    def upsert(self, profile: Profile) -> bool: ...

    def find_by_id(self, account_id: UUID) -> Profile | None: ...
