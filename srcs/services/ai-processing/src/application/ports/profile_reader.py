from typing import Protocol


class ProfileReader(Protocol):
    def get_topic_ids(self, user_token: str) -> tuple[str, ...]:
        """Return the topics the token's account follows, in the profile's order.

        The user's token is forwarded unchanged (ADR-0008: the profile is the
        user's data): Personalization reads the account from it.

        Returns an empty tuple if the account has no profile yet.

        Raises:
            TokenExpiredError: if the token expired on the way.
            InfrastructureError: if Personalization can't be reached or answers
                with an unexpected response.
        """
        ...
