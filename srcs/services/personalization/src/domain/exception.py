"""
Domain Layer errors.
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_NAME = "INVALID_NAME"
    INVALID_INTERESTS = "INVALID_INTERESTS"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    INVALID_ACCOUNT_ID = "INVALID_ACCOUNT_ID"


class DomainError(Exception):
    code: ErrorCode

    def __init__(self, message: str):
        super().__init__(message)


class InvalidNameError(DomainError):
    code = ErrorCode.INVALID_NAME

    def __init__(self):
        super().__init__("Invalid name")


class InvalidInterestsError(DomainError):
    code = ErrorCode.INVALID_INTERESTS

    def __init__(self):
        super().__init__("Invalid interests")


class ProfileNotFoundError(DomainError):
    code = ErrorCode.PROFILE_NOT_FOUND

    def __init__(self):
        super().__init__("Profile not found")


class InvalidAccountIdError(DomainError):
    code = ErrorCode.INVALID_ACCOUNT_ID

    def __init__(self):
        super().__init__("Missing or invalid account id")
