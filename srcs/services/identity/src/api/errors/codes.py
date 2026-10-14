from dataclasses import dataclass

from fastapi import status

from src.api.errors.exceptions import ApiErrorCode
from src.domain.exception import ErrorCode


@dataclass(frozen=True)
class HttpErrorConfig:
    status_code: int
    headers: dict[str, str] | None = None


DOMAIN_ERROR_STATUS_MAP: dict[ErrorCode, HttpErrorConfig] = {
    ErrorCode.INVALID_EMAIL: HttpErrorConfig(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    ),
    ErrorCode.INVALID_PASSWORD_HASH: HttpErrorConfig(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    ),
    ErrorCode.EMAIL_ALREADY_REGISTERED: HttpErrorConfig(
        status_code=status.HTTP_409_CONFLICT
    ),
    ErrorCode.INVALID_CREDENTIALS: HttpErrorConfig(
        status_code=status.HTTP_401_UNAUTHORIZED
    ),
    ErrorCode.INVALID_TOKEN: HttpErrorConfig(
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"}
    ),
    ErrorCode.TOKEN_EXPIRED: HttpErrorConfig(
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"}
    ),
    ErrorCode.TOKEN_REVOKED: HttpErrorConfig(
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"}
    ),
}

API_ERROR_STATUS_MAP: dict[ApiErrorCode, HttpErrorConfig] = {
    ApiErrorCode.CSRF_CHECK_FAILED: HttpErrorConfig(
        status_code=status.HTTP_403_FORBIDDEN
    ),
}
