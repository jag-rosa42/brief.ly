from fastapi import status

from src.domain.exception import ErrorCode

DOMAIN_ERROR_STATUS_MAP: dict[ErrorCode, int] = {
    ErrorCode.INVALID_EMAIL: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ErrorCode.INVALID_PASSWORD_HASH: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ErrorCode.EMAIL_ALREADY_REGISTERED: status.HTTP_409_CONFLICT,
}
