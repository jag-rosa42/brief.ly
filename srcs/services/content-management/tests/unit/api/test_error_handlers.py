from json import loads
from unittest.mock import Mock

from src.api.errors.exceptions import ArticleIngestionFailedError
from src.api.errors.handlers import api_error_handler, domain_error_handler
from src.domain.exception import ArticleIngestionAlreadyRunningError, TopicNotFoundError


def test_maps_ingestion_failure_to_structured_502() -> None:
    response = api_error_handler(Mock(), ArticleIngestionFailedError())

    assert response.status_code == 502
    assert loads(bytes(response.body)) == {
        "error": {
            "code": "ARTICLE_INGESTION_FAILED",
            "message": "Article ingestion completed with errors.",
        }
    }


def test_maps_concurrent_ingestion_to_structured_409() -> None:
    response = domain_error_handler(Mock(), ArticleIngestionAlreadyRunningError())

    assert response.status_code == 409
    assert loads(bytes(response.body)) == {
        "error": {
            "code": "ARTICLE_INGESTION_ALREADY_RUNNING",
            "message": "An article ingestion run is already in progress.",
        }
    }


def test_maps_unknown_topic_to_structured_404() -> None:
    response = domain_error_handler(Mock(), TopicNotFoundError("unknown"))

    assert response.status_code == 404
    assert loads(bytes(response.body)) == {
        "error": {
            "code": "TOPIC_NOT_FOUND",
            "message": "Topic 'unknown' was not found.",
        }
    }
