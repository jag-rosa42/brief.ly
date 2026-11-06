from enum import StrEnum


class ApiErrorCode(StrEnum):
    CSRF_CHECK_FAILED = "CSRF_CHECK_FAILED"
    UNSUPPORTED_GRANT_TYPE = "UNSUPPORTED_GRANT_TYPE"

class ApiError(Exception):
    code: ApiErrorCode

    def __init__(self, message: str):
        super().__init__(message)


class CsrfCheckFailedError(ApiError):
    code = ApiErrorCode.CSRF_CHECK_FAILED

    def __init__(self):
        super().__init__("Missing or invalid client header")


class UnsupportedGrantTypeError(ApiError):
    # OAuth 2.0 error unsupported_grant_type (RFC 6749 §5.2): the token
    # endpoint only implements client credentials.
    code = ApiErrorCode.UNSUPPORTED_GRANT_TYPE

    def __init__(self):
        super().__init__("Only grant_type=client_credentials is supported")
