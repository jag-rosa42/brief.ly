import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared_errors.handlers import respond
from shared_errors.schemas import ErrorBody, ErrorDetails
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from src.api.errors.codes import DOMAIN_ERROR_STATUS_MAP, HttpErrorConfig
from src.domain.exception import DomainError

logger: logging.Logger = logging.getLogger(__name__)


def domain_error_handler(_request: Request, exception: Exception) -> JSONResponse:
    """Handle domain errors and map them to appropriate HTTP responses.

    The domain error code is used to determine the corresponding HTTP status
    code from ``DOMAIN_ERROR_STATUS_MAP``. If the error code is not explicitly
    mapped, the missing mapping is logged and the handler defaults to HTTP 500
    Internal Server Error.

    Args:
        _request: The incoming HTTP request. Unused by this handler.
        exception: The domain error that was raised.

    Returns:
        A JSON response containing the domain error code and message, with
        the HTTP status code defined by ``DOMAIN_ERROR_STATUS_MAP`` or 500
        when no explicit mapping exists.
    """

    # TODO: `assert isinstance(...)` is stripped when Python runs with -O (optimized mode)
    # which would remove this narrowing at runtime. Not an issue as long as nothing in our
    # deployment sets -O / PYTHONOPTIMIZE, but worth confirming before prod — check the
    # Dockerfile CMD/ENTRYPOINT and any uvicorn/gunicorn launch flags for -O or -OO.
    # If we ever do need -O, switch this to `cast(ExceptionHandler, domain_error_handler)`
    # instead, which has no runtime footprint either way.
    assert isinstance(exception, DomainError)

    config: HttpErrorConfig | None = DOMAIN_ERROR_STATUS_MAP.get(exception.code)

    if config is None:
        logger.error("No HTTP status mapped for DomainError code: %s", exception.code)
        config = HttpErrorConfig(status_code=HTTP_500_INTERNAL_SERVER_ERROR)

    details: list[ErrorDetails] | None = [
        ErrorDetails(field=detail.field, message=detail.message, type=detail.type)
        for detail in exception.details
    ] or None
    return respond(
        config.status_code,
        ErrorBody(code=exception.code, message=str(exception), details=details),
        headers=config.headers,
    )


def register_domain_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
