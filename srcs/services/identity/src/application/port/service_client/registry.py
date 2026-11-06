from typing import Protocol

from src.domain.entities.service_client import ServiceClient


class ServiceClientRegistry(Protocol):
    """Which service clients exist, and what each one may ask for."""

    def find(self, client_id: str) -> ServiceClient | None:
        """Return the client, or None when no client has this ID."""
        ...
