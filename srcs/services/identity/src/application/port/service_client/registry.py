from typing import Protocol

from src.domain.entities.service_client import ServiceClient


# "Service" is kept although the folder says it too: the class is imported
# without its folder, and Identity has other kinds of clients (the browser,
# public API callers).
class ServiceClientRegistry(Protocol):
    """Which service clients exist, and what each one may ask for."""

    def find(self, client_id: str) -> ServiceClient | None:
        """Return the client, or None when no client has this ID."""
        ...

    def client_ids(self) -> frozenset[str]:
        """Return the ID of every client.

        The secret verifier builds file names only from these IDs, so an ID
        sent in a request can never point to another secret file.
        """
        ...
