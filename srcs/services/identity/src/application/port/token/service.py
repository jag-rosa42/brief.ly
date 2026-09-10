from typing import Protocol
from uuid import UUID

from src.application.port.token.types import AccessTokenPayload


class TokenService(Protocol):
    def create_access_token(self, account_id: UUID) -> str: ...

    def decode_access_token(self, token: str) -> AccessTokenPayload: ...
