from typing import Protocol

from src.domain.entities.profile import Profile


class ProfileReader(Protocol):
    def get(self, user_token: str) -> Profile | None:
        """Return the profile of the token's account, as Personalization knows it.

        The user's token is forwarded unchanged: Personalization reads the
        account from it.

        Returns None if the account has no profile yet.

        Raises:
            TokenExpiredError: if the token expired on the way.
            InfrastructureError: if Personalization can't be reached or answers
                with an unexpected response.
        """
        ...
