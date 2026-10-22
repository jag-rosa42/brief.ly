from typing import Protocol

from shared_auth.domain.verified_token import VerifiedToken


class TokenVerifier(Protocol):
    def verify(self, token: str) -> VerifiedToken: ...
