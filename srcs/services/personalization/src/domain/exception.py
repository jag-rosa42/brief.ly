"""
Domain Layer errors.
"""

from dataclasses import dataclass
from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_NAME = "INVALID_NAME"
    INVALID_INTERESTS = "INVALID_INTERESTS"
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    INVALID_ACCOUNT_ID = "INVALID_ACCOUNT_ID"
    VALIDATION_ERROR = "VALIDATION_ERROR"


@dataclass(frozen=True)
class FieldError:
    field: str
    message: str
    type: str


class DomainError(Exception):
    code: ErrorCode
    details: tuple[FieldError, ...] = ()

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


class UnknownTopicsError(DomainError):
    code = ErrorCode.VALIDATION_ERROR

    def __init__(self, topic_ids: set[str]):
        self.topic_ids: set[str] = topic_ids
        self.details = tuple(
            FieldError(
                field="topic_ids",
                message=f"Unknown topic id: {topic_id}",
                type="unknown_topic",
            )
            for topic_id in sorted(topic_ids)
        )
        super().__init__("Unknown topic ids")


class ProfileFieldsRequiredError(DomainError):
    code = ErrorCode.VALIDATION_ERROR

    def __init__(self, missing_fields: list[str]):
        self.details = tuple(
            FieldError(
                field=field,
                message="Required to create a profile",
                type="missing",
            )
            for field in missing_fields
        )
        super().__init__("name and topic_ids are required to create a profile")
