from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INSUFFICIENT_SCOPE = "INSUFFICIENT_SCOPE"
    DOWNSTREAM_ERROR = "DOWNSTREAM_ERROR"


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


# Follow RFC6750 error code: https://www.rfc-editor.org/info/rfc6750/#section-3.1
class InsufficientScopeError(AuthenticationError):
    code = ErrorCode.INSUFFICIENT_SCOPE

    def __init__(self, missing: frozenset[str]) -> None:
        super().__init__(f"Missing scope: {' '.join(sorted(missing))}")
        self.missing: frozenset[str] = missing
