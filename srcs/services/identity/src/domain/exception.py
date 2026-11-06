"""
Domain Layer errors.
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PASSWORD_HASH = "INVALID_PASSWORD_HASH"
    EMAIL_ALREADY_REGISTERED = "EMAIL_ALREADY_REGISTERED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    INVALID_CLIENT = "INVALID_CLIENT"
    INVALID_SCOPE = "INVALID_SCOPE"


class DomainError(Exception):
    code: ErrorCode

    def __init__(self, message: str):
        super().__init__(message)


class InvalidEmail(DomainError):
    code = ErrorCode.INVALID_EMAIL

    def __init__(self):
        super().__init__("Invalid email address")


class InvalidPasswordHash(DomainError):
    code = ErrorCode.INVALID_PASSWORD_HASH

    def __init__(self):
        super().__init__("Invalid password hash")


class EmailAlreadyRegisteredError(DomainError):
    code = ErrorCode.EMAIL_ALREADY_REGISTERED

    def __init__(self):
        super().__init__("Email already registered")


class InvalidCredentialsError(DomainError):
    code = ErrorCode.INVALID_CREDENTIALS

    def __init__(self):
        # super().__init__("Invalid email or password")
        super().__init__("Could not validate credentials")


class InvalidTokenError(DomainError):
    code = ErrorCode.INVALID_TOKEN

    def __init__(self):
        super().__init__("Token not recognised")


class TokenExpiredError(DomainError):
    code = ErrorCode.TOKEN_EXPIRED

    def __init__(self):
        super().__init__("Token has expired")


class TokenRevokedError(DomainError):
    code = ErrorCode.TOKEN_REVOKED

    def __init__(self):
        super().__init__("Token has already been used")


# Client credentials (ADR-0008). The names follow the OAuth 2.0 error codes
# (RFC 6749 §5.2: invalid_client, invalid_scope), written in our format.
class InvalidClientError(DomainError):
    code = ErrorCode.INVALID_CLIENT

    def __init__(self):
        super().__init__("Client authentication failed")


class InvalidScopeError(DomainError):
    code = ErrorCode.INVALID_SCOPE

    def __init__(self):
        super().__init__("Requested audience or scope is not allowed for this client")
