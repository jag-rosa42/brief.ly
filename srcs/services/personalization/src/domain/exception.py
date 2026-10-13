"""
Domain Layer errors.
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_NAME = "INVALID_NAME"
    INVALID_INTERESTS = "INVALID_INTERESTS"


class DomainError(Exception):
    code: ErrorCode

    def __init__(self, message: str):
        super().__init__(message)


class InvalidName(DomainError):
    code = ErrorCode.INVALID_NAME

    def __init__(self):
        super().__init__("Invalid name")


class InvalidInterests(DomainError):
    code = ErrorCode.INVALID_INTERESTS

    def __init__(self):
        super().__init__("Invalid interests")
