from json import loads
from unittest.mock import Mock

from src.api.errors.exceptions import IngestionFailedError
from src.api.errors.handlers import api_error_handler, domain_error_handler
from src.domain.exception import IngestionAlreadyRunningError


def test_maps_ingestion_failure_to_structured_500() -> None:
    response = api_error_handler(Mock(), IngestionFailedError())

    assert response.status_code == 500
    assert loads(bytes(response.body)) == {
        "error": {
            "code": "INGESTION_FAILED",
            "message": "Article ingestion completed with errors.",
        }
    }


def test_maps_concurrent_ingestion_to_structured_409() -> None:
    response = domain_error_handler(Mock(), IngestionAlreadyRunningError())

    assert response.status_code == 409
    assert loads(bytes(response.body)) == {
        "error": {
            "code": "INGESTION_ALREADY_RUNNING",
            "message": "An article ingestion run is already in progress.",
        }
    }
