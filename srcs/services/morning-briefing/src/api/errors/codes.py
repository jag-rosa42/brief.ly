from dataclasses import dataclass

from fastapi import status

from src.domain.exception import ErrorCode


@dataclass(frozen=True)
class HttpErrorConfig:
    status_code: int
    headers: dict[str, str] | None = None


DOMAIN_ERROR_STATUS_MAP: dict[ErrorCode, HttpErrorConfig] = {
    ErrorCode.PROFILE_NOT_FOUND: HttpErrorConfig(status_code=status.HTTP_404_NOT_FOUND),
}
