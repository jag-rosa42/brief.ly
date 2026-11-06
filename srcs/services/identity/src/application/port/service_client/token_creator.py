from typing import Protocol

from src.application.port.token.types import CreatedServiceToken


class ServiceTokenCreator(Protocol):
    """Creates service tokens (ADR-0007, ADR-0008).

    Kept apart from TokenService: account sessions never need service tokens,
    and the client credentials use case needs nothing else.
    """

    def create_service_token(
        self,
        client_id: str,
        audience: str,
        scopes: frozenset[str],
    ) -> CreatedServiceToken:
        """Sign a token with `sub=service:<client_id>`, this audience and scopes."""
        ...
