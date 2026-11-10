from typing import Protocol
from uuid import UUID

from src.domain.entities.api_key import ApiKeyScope


class PublicApiTokenCreator(Protocol):
    """Creates public API tokens (ADR-0007, ADR-0009).

    Kept apart from TokenService, like ServiceTokenCreator: account sessions
    never need public API tokens, and key verification needs nothing else.
    """

    def create_public_api_token(
        self,
        account_id: UUID,
        scopes: frozenset[ApiKeyScope],
    ) -> str:
        """Sign a short-lived access token for the public API audience."""
        ...
