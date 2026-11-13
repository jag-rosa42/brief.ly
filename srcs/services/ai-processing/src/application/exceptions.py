"""
Application Layer errors.

Both are InfrastructureError: shared_errors answers them with
503 SERVICE_UNAVAILABLE, before the stream starts.
"""

from shared_errors.exceptions import InfrastructureError


class ProfileReaderUnavailableError(InfrastructureError):
    def __init__(self) -> None:
        super().__init__("profile reader unavailable")


class TopicCatalogUnavailableError(InfrastructureError):
    def __init__(self) -> None:
        super().__init__("topic catalog unavailable")
