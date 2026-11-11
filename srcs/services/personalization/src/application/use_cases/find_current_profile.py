from uuid import UUID

from src.domain.entities.profile import Profile
from src.domain.repositories.profile_repository import ProfileRepository


class FindCurrentProfile:
    """The caller's profile, or None when they haven't created it yet.

    Right after sign-up there is no profile, and that is a normal state (the
    app shows the profile form), not an error. Answering 404 made Chrome log a
    red error in the console for every new user.
    """

    def __init__(self, profile_repository: ProfileRepository) -> None:
        self._profiles: ProfileRepository = profile_repository

    def execute(self, account_id: UUID) -> Profile | None:
        return self._profiles.find_by_id(account_id)
