from typing import Protocol


class TokenProvider(Protocol):
    """Anything that gives a valid service token, like shared_auth's
    ClientCredentialsTokenProvider. Tests pass a fake one."""

    def get_token(self) -> str: ...
