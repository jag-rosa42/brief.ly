import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from shared_errors.handlers import respond
from shared_errors.schemas import ErrorBody

from src.api.errors.codes import (
    API_ERROR_STATUS_MAP,
    DOMAIN_ERROR_STATUS_MAP,
    HttpErrorConfig,
)
from src.api.errors.exceptions import ApiError
from src.domain.exception import DomainError

logger = logging.getLogger(__name__)


def _error_response(
    exception: ApiError | DomainError,
    config: HttpErrorConfig | None,
) -> JSONResponse:
    if config is None:
        logger.error("No HTTP status mapped for error code: %s", exception.code)
        config = HttpErrorConfig(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return respond(
        config.status_code,
        ErrorBody(code=exception.code, message=str(exception)),
        headers=config.headers,
    )


def domain_error_handler(_request: Request, exception: Exception) -> JSONResponse:
    assert isinstance(exception, DomainError)
    return _error_response(exception, DOMAIN_ERROR_STATUS_MAP.get(exception.code))


def api_error_handler(_request: Request, exception: Exception) -> JSONResponse:
    assert isinstance(exception, ApiError)
    return _error_response(exception, API_ERROR_STATUS_MAP.get(exception.code))


def register_domain_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)


def register_api_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, api_error_handler)
