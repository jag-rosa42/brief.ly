from uuid import UUID

from src.domain.entities.profile import Profile
from src.domain.exception import ProfileNotFoundError
from src.domain.repositories.profile_repository import ProfileRepository


class GetCurrentProfile:
    def __init__(self, profile_repository: ProfileRepository) -> None:
        self._profiles: ProfileRepository = profile_repository

    def execute(self, account_id: UUID) -> Profile:
        profile: Profile | None = self._profiles.find_by_id(account_id)
        if profile is None:
            raise ProfileNotFoundError()
        return profile
