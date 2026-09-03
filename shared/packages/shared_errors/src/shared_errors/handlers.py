"""FastAPI exception handlers shared across applications.

This module provides a consistent error-response format for:
- Request validation errors (HTTP 422).
- Unexpected/unhandled exceptions (HTTP 500).

The handlers are registered through `register_shared_handlers()`, allowing
applications that use this package to share the same error-handling behavior.
"""

import logging
from collections.abc import Sequence

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler

from shared_errors.exceptions import InfrastructureError
from shared_errors.schemas import ErrorBody, ErrorDetails, ErrorResponse

logger: logging.Logger = logging.getLogger(__name__)


# ============================================================================
# Response Helpers
# ============================================================================
def respond(status_code: int, body: ErrorBody) -> JSONResponse:
    """Build a JSON response using the shared error-response schema.

    Args:
        status_code: HTTP status code to return.
        body: Structured error information to include in the response.

    Returns:
        A JSONResponse containing the serialized ErrorResponse.
    """
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=body).model_dump(exclude_none=True),
    )


# ============================================================================
# Exception Handlers
# ============================================================================
def validation_exception_handler(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    """Handle FastAPI request validation errors.

    FastAPI/Starlette requires exception handlers to accept `Exception` as
    their second parameter, even when a handler is registered for a more
    specific exception type.

    The assertion narrows `exception` from the generic `Exception` type to
    `RequestValidationError`, allowing access to its `.errors()` method.

    Args:
        _request: The incoming HTTP request. Unused by this handler.
        exception: The exception raised during request validation.

    Returns:
        A 422 response containing all validation errors.
    """
    # Type narrowing: add_exception_handler() requires a handler that accepts
    # any Exception, but this handler is registered specifically for
    # RequestValidationError. After this assertion, the type checker knows
    # that `exception` is a RequestValidationError.
    # TODO: `assert isinstance(...)` is stripped when Python runs with -O (optimized mode)
    assert isinstance(exception, RequestValidationError)

    details: list[ErrorDetails] = []

    for err in exception.errors():
        parts: list[str] = []

        for p in err["loc"]:
            if p != "body":
                parts.append(str(p))

        field: str = ".".join(parts)

        details.append(
            ErrorDetails(
                field=field,
                message=err["msg"],
                type=err["type"],
            )
        )
    return respond(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        body=ErrorBody(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            details=details,
        ),
    )


def unexpected_exception_handler(_request: Request, exception: Exception) -> JSONResponse:
    """Handle unexpected exceptions with a generic 500 response.

    The full exception and traceback are logged server-side, while the
    client receives a generic message without internal implementation
    details.

    Args:
        _request: The incoming HTTP request. Unused by this handler.
        exception: The unexpected exception that was raised.

    Returns:
        A 500 response containing a generic internal-server-error message.
    """
    logger.error("Unhandled exception", exc_info=exception)
    return respond(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        body=ErrorBody(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred.",
        ),
    )


def infrastructure_error_handler(_request: Request, exception: Exception) -> JSONResponse:
    """Handle infrastructure errors with a 503 Service Unavailable response.

    Infrastructure errors indicate that a required external dependency or
    infrastructure component is currently unavailable. The full exception
    and traceback are logged server-side, while the client receives a
    structured error response.

    Args:
        _request: The incoming HTTP request. Unused by this handler.
        exception: The infrastructure error that was raised.

    Returns:
        A 503 response indicating that the required service is unavailable.
    """
    logger.error("Infrastructure dependency unavailable", exc_info=exception)
    return respond(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        body=ErrorBody(
            code="SERVICE_UNAVAILABLE",
            message=str(exception),
        ),
    )


# ============================================================================
# Exception Handler Registration
# ============================================================================
# Starlette's ExceptionHandler type represents a callable that accepts
# (Request, Exception) and returns a Response, or an awaitable Response.
#
# Sequence is used because the handlers are iterated over but never modified.
# Each tuple maps an exception class to the handler responsible for it.
ERROR_HANDLERS: Sequence[tuple[type[Exception], ExceptionHandler]] = (
    (RequestValidationError, validation_exception_handler),
    (InfrastructureError, infrastructure_error_handler),
    (Exception, unexpected_exception_handler),
)


def register_shared_handlers(app: FastAPI) -> None:
    for exception_type, handler in ERROR_HANDLERS:
        app.add_exception_handler(exception_type, handler)
