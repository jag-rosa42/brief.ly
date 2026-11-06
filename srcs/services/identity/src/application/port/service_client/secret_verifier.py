from typing import Protocol


class ClientSecretVerifier(Protocol):
    """Checks a service client's secret."""

    def verify(self, client_id: str, client_secret: str) -> bool:
        """True only when the secret is the one stored for this client.

        An unknown client, or a client whose secret is not configured, is
        never accepted. Implementations compare in constant time, so the
        response time doesn't reveal how much of the secret was right.
        """
        ...
