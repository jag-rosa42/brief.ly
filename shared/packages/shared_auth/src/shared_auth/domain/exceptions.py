from enum import StrEnum

from fastapi import status


class ErrorCode(StrEnum):
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"


class AuthenticationError(Exception):
    code: ErrorCode

    def __init__(self, message: str):
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    code = ErrorCode.INVALID_TOKEN

    def __init__(self):
        super().__init__("Token not recognised")


class TokenExpiredError(AuthenticationError):
    code = ErrorCode.TOKEN_EXPIRED

    def __init__(self):
        super().__init__("Token has expired")
