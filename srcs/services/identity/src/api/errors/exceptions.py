from enum import StrEnum


class ApiErrorCode(StrEnum):
    CSRF_CHECK_FAILED = "CSRF_CHECK_FAILED"


class ApiError(Exception):
    code: ApiErrorCode

    def __init__(self, message: str):
        super().__init__(message)


class CsrfCheckFailedError(ApiError):
    code = ApiErrorCode.CSRF_CHECK_FAILED

    def __init__(self):
        super().__init__("Missing or invalid client header")
