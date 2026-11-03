"""
Application Layer errors.
"""

from shared_errors.exceptions import InfrastructureError


class TopicCatalogUnavailableError(InfrastructureError):
    def __init__(self) -> None:
        super().__init__("topic catalog unavailable")
