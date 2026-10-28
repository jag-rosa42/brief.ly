from collections.abc import Generator
from datetime import UTC
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_errors import ErrorResponse

from src.api.dependencies.ingestion import get_synchronize_sources
from src.application.use_cases.ingestion import SynchronizationResult
from src.domain.exception import ArticleIngestionAlreadyRunningError
from src.main import app
from tests import routes


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def synchronize_sources() -> Generator[Mock]:
    use_case = Mock()
    app.dependency_overrides[get_synchronize_sources] = lambda: use_case
    yield use_case
    app.dependency_overrides.pop(get_synchronize_sources, None)


def test_returns_201_when_ingestion_succeeds(
    client: TestClient,
    synchronize_sources: Mock,
) -> None:
    synchronize_sources.execute.return_value = SynchronizationResult()

    response: Response = client.post(routes.INGESTION_RUNS)

    assert response.status_code == 201
    assert response.json() == {"status": "succeeded"}
    synchronized_at = synchronize_sources.execute.call_args.args[0]
    assert synchronized_at.tzinfo is UTC


def test_returns_201_when_ingestion_partially_succeeds(
    client: TestClient,
    synchronize_sources: Mock,
) -> None:
    synchronize_sources.execute.return_value = SynchronizationResult(
        failures=1,
        sources_succeeded=1,
        sources_failed=1,
    )

    response: Response = client.post(routes.INGESTION_RUNS)

    assert response.status_code == 201
    assert response.json() == {"status": "partial"}


def test_returns_structured_502_when_ingestion_fails(
    client: TestClient,
    synchronize_sources: Mock,
) -> None:
    synchronize_sources.execute.return_value = SynchronizationResult(
        failures=1,
        sources_failed=1,
    )

    response: Response = client.post(routes.INGESTION_RUNS)

    assert response.status_code == 502
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "ARTICLE_INGESTION_FAILED"
    assert body.error.message == "Article ingestion completed with errors."


def test_returns_409_when_an_ingestion_is_already_running(
    client: TestClient,
    synchronize_sources: Mock,
) -> None:
    synchronize_sources.execute.side_effect = ArticleIngestionAlreadyRunningError()

    response: Response = client.post(routes.INGESTION_RUNS)

    assert response.status_code == 409
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "ARTICLE_INGESTION_ALREADY_RUNNING"


def test_exposes_only_the_collection_post_operation() -> None:
    ingestion_run_paths = {
        path: path_item
        for path, path_item in app.openapi()["paths"].items()
        if path.startswith(routes.INGESTION_RUNS)
    }

    assert set(ingestion_run_paths) == {routes.INGESTION_RUNS}
    assert set(ingestion_run_paths[routes.INGESTION_RUNS]) == {"post"}
    responses = ingestion_run_paths[routes.INGESTION_RUNS]["post"]["responses"]
    assert {"201", "409", "500", "502"} <= set(responses)
