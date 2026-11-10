from dataclasses import dataclass

from fastapi import status

from src.api.errors.exceptions import ApiErrorCode
from src.domain.exception import ErrorCode


@dataclass(frozen=True)
class HttpErrorConfig:
    status_code: int
    headers: dict[str, str] | None = None


_H400 = status.HTTP_400_BAD_REQUEST
_H401 = status.HTTP_401_UNAUTHORIZED
_H409 = status.HTTP_409_CONFLICT
_H422 = status.HTTP_422_UNPROCESSABLE_CONTENT


DOMAIN_ERROR_STATUS_MAP: dict[ErrorCode, HttpErrorConfig] = {
    ErrorCode.INVALID_EMAIL: HttpErrorConfig(
        status_code=_H422,
    ),
    ErrorCode.INVALID_PASSWORD_HASH: HttpErrorConfig(
        status_code=_H422,
    ),
    ErrorCode.EMAIL_ALREADY_REGISTERED: HttpErrorConfig(status_code=_H409),
    ErrorCode.INVALID_CREDENTIALS: HttpErrorConfig(
        status_code=_H401,
    ),
    ErrorCode.INVALID_TOKEN: HttpErrorConfig(
        status_code=_H401, headers={"WWW-Authenticate": "Bearer"}
    ),
    ErrorCode.TOKEN_EXPIRED: HttpErrorConfig(
        status_code=_H401, headers={"WWW-Authenticate": "Bearer"}
    ),
    ErrorCode.TOKEN_REVOKED: HttpErrorConfig(
        status_code=_H401, headers={"WWW-Authenticate": "Bearer"}
    ),
    # RFC 6749 §5.2: a client that authenticated with HTTP Basic gets 401
    # and the header naming the scheme to use.
    ErrorCode.INVALID_CLIENT: HttpErrorConfig(
        status_code=_H401, headers={"WWW-Authenticate": "Basic"}
    ),
    ErrorCode.INVALID_SCOPE: HttpErrorConfig(
        status_code=_H400,
    ),
    ErrorCode.API_KEY_LIMIT_REACHED: HttpErrorConfig(
        status_code=_H409,
    ),
}


API_ERROR_STATUS_MAP: dict[ApiErrorCode, HttpErrorConfig] = {
    ApiErrorCode.CSRF_CHECK_FAILED: HttpErrorConfig(
        status_code=status.HTTP_403_FORBIDDEN
    ),
    ApiErrorCode.UNSUPPORTED_GRANT_TYPE: HttpErrorConfig(
        status_code=_H400,
    ),
}
