"""FastAPI exception handlers for authentication and downstream errors.

Responses use the shared error format (shared_errors.ErrorResponse), so a
TOKEN_EXPIRED looks the same whether it comes from Identity, from this
service, or from a service further down the chain.

InfrastructureError (a dead or slow service -> 503) is already handled by
shared_errors.register_shared_exception_handlers, which every service registers.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared_errors import ErrorBody
from shared_errors.handlers import respond

from shared_auth.api.errors.codes import AUTHENTICATION_ERROR_STATUS_MAP, HttpErrorConfig
from shared_auth.domain.exceptions import AuthenticationError
from shared_auth.infrastructure.clients.exceptions import DownstreamError

logger: logging.Logger = logging.getLogger(__name__)


def auth_errors_handlers(_request: Request, exception: Exception) -> JSONResponse:
    # Type narrowing, same pattern as shared_errors (see the TODO there
    # about `assert` and `python -O`).
    assert isinstance(exception, AuthenticationError)
    config: HttpErrorConfig = AUTHENTICATION_ERROR_STATUS_MAP[exception.code]
    return respond(
        config.status_code,
        ErrorBody(code=exception.code, message=str(exception)),
        headers=config.headers,
    )


def downstream_errors_handlers(_request: Request, exception: Exception) -> JSONResponse:
    assert isinstance(exception, DownstreamError)

    # The details (which service, which status) are logged for us, not sent to the client
    logger.error("Downstream call failed: %s", exception)
    config: HttpErrorConfig = AUTHENTICATION_ERROR_STATUS_MAP[DownstreamError.code]
    return respond(
        config.status_code,
        ErrorBody(
            code=DownstreamError.code,
            message="A downstream service returned an unexpected error.",
        ),
        headers=config.headers,
    )


def configure_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AuthenticationError, auth_errors_handlers)
    app.add_exception_handler(DownstreamError, downstream_errors_handlers)
