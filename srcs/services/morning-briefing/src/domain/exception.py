"""
Domain Layer errors.
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"


class DomainError(Exception):
    code: ErrorCode

    def __init__(self, message: str):
        super().__init__(message)


class ProfileNotFoundError(DomainError):
    code = ErrorCode.PROFILE_NOT_FOUND

    def __init__(self):
        super().__init__("Profile not found")
