from dataclasses import dataclass

from fastapi import status

from shared_auth.domain.exceptions import ErrorCode


@dataclass(frozen=True)
class HttpErrorConfig:
    status_code: int
    headers: dict[str, str] | None = None


_H401 = status.HTTP_401_UNAUTHORIZED
_H403 = status.HTTP_403_FORBIDDEN
_H502 = status.HTTP_502_BAD_GATEWAY

AUTHENTICATION_ERROR_STATUS_MAP: dict[ErrorCode, HttpErrorConfig] = {
    ErrorCode.INVALID_TOKEN: HttpErrorConfig(
        status_code=_H401,
        headers={"WWW-Authenticate": "Bearer"},
    ),
    ErrorCode.TOKEN_EXPIRED: HttpErrorConfig(
        status_code=_H401,
        headers={"WWW-Authenticate": "Bearer"},
    ),
    ErrorCode.INSUFFICIENT_SCOPE: HttpErrorConfig(
        status_code=_H403,
    ),
    ErrorCode.DOWNSTREAM_ERROR: HttpErrorConfig(
        status_code=_H502,
    ),
}
