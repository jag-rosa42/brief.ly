from dataclasses import dataclass

from fastapi import status

from src.api.errors.exceptions import ApiErrorCode
from src.domain.exception import ErrorCode


@dataclass(frozen=True)
class HttpErrorConfig:
    status_code: int
    headers: dict[str, str] | None = None


DOMAIN_ERROR_STATUS_MAP: dict[ErrorCode, HttpErrorConfig] = {
    ErrorCode.INGESTION_ALREADY_RUNNING: HttpErrorConfig(
        status_code=status.HTTP_409_CONFLICT
    ),
}

API_ERROR_STATUS_MAP: dict[ApiErrorCode, HttpErrorConfig] = {
    ApiErrorCode.INGESTION_FAILED: HttpErrorConfig(
        status_code=status.HTTP_502_BAD_GATEWAY
    ),
}
