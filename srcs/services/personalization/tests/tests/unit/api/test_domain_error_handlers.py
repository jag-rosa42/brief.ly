from fastapi.testclient import TestClient
from shared_errors import ErrorResponse

from src.domain.exception import DomainError, InvalidInterests, InvalidName
from src.main import create_app


def _client_raising(error: DomainError) -> TestClient:
    app = create_app()

    @app.get("/raise")
    def raise_error() -> None:
        raise error

    return TestClient(app)


def test_invalid_name_returns_422() -> None:
    response = _client_raising(InvalidName()).get("/raise")

    assert response.status_code == 422
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "INVALID_NAME"


def test_invalid_interests_returns_422() -> None:
    response = _client_raising(InvalidInterests()).get("/raise")

    assert response.status_code == 422
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "INVALID_INTERESTS"
