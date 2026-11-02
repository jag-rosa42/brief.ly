import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response
from pydantic import BaseModel, EmailStr

from shared_errors import (
    ErrorResponse,
    InfrastructureError,
    register_shared_exception_handlers,
)


def _build_test_app() -> FastAPI:
    app = FastAPI()
    register_shared_exception_handlers(app)

    class Payload(BaseModel):
        email: EmailStr

    @app.post("/validate")
    def validate(payload: Payload) -> dict[str, str]:
        return {"email": payload.email}

    @app.get("/infra-error")
    def infra_error() -> None:
        raise InfrastructureError("Database unavailable")

    @app.get("/unknow")
    def runtime_error() -> None:
        raise RuntimeError("An unexpected error occurred while processing the request.")

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_build_test_app())


@pytest.fixture
def client_allowing_server_errors() -> TestClient:
    return TestClient(_build_test_app(), raise_server_exceptions=False)


def test_validation_error_returns_consistent_response_format(client: TestClient) -> None:
    response: Response = client.post("/validate", json={"email": "not-an-email"})

    assert response.status_code == 422
    body: ErrorResponse = ErrorResponse.model_validate(response.json())

    assert body.error.code == "VALIDATION_ERROR"
    assert body.error.message == "Request validation failed."
    assert body.error.details is not None
    assert body.error.details[0].field == "email"


def test_infrastructure_error_returns_503_response_format(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR):
        response: Response = client.get("/infra-error")

    assert any(
        record.levelno == logging.ERROR
        and record.message == "Infrastructure dependency unavailable"
        and record.exc_info is not None
        for record in caplog.records
    )

    assert response.status_code == 503

    body: ErrorResponse = ErrorResponse.model_validate(response.json())
    assert body.error.code == "SERVICE_UNAVAILABLE"
    assert body.error.message == "Database unavailable"
    assert body.error.details is None


def test_unexpected_exception_returns_500_reponse_format(
    client_allowing_server_errors: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR):
        response: Response = client_allowing_server_errors.get("/unknow")

    assert any(
        record.levelno == logging.ERROR
        and record.message == "Unhandled exception"
        and record.exc_info is not None
        for record in caplog.records
    )
    assert response.status_code == 500

    body: ErrorResponse = ErrorResponse.model_validate(response.json())
    assert body.error.code == "INTERNAL_SERVER_ERROR"
    assert body.error.message == "An unexpected error occurred."
    assert body.error.details is None
