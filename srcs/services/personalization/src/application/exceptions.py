"""
Application Layer errors.
"""

from enum import StrEnum

from shared_errors.exceptions import InfrastructureError


class ErrorCode(StrEnum):
    INVALID_NAME = "INVALID_NAME"
    INVALID_INTERESTS = "INVALID_INTERESTS"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    INVALID_ACCOUNT_ID = "INVALID_ACCOUNT_ID"


class TopicCatalogUnavailableError(InfrastructureError):
    def __init__(self) -> None:
        super().__init__("topic catalog unavailable")
