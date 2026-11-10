import time
from collections.abc import Generator
from datetime import UTC
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from prometheus_client import REGISTRY
from shared_errors import ErrorResponse

from src.api.dependencies.ingestion import get_synchronize_sources
from src.application.use_cases.ingestion import SynchronizationResult
from src.domain.exception import ArticleIngestionAlreadyRunningError
from src.main import app
from tests import routes


def metric_value(name: str, labels: dict[str, str] | None = None) -> float:
    return REGISTRY.get_sample_value(name, labels or {}) or 0.0


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
    synchronize_sources.execute.return_value = SynchronizationResult(articles_created=2)
    runs_before = metric_value("content_ingestion_runs_total", {"outcome": "succeeded"})
    articles_before = metric_value("content_ingestion_articles_created_total")
    failures_before = metric_value("content_ingestion_failures_total")
    started_at = time.time()

    response: Response = client.post(routes.INGESTION_RUNS)

    assert response.status_code == 201
    assert response.json() == {"status": "succeeded"}
    synchronized_at = synchronize_sources.execute.call_args.args[0]
    assert synchronized_at.tzinfo is UTC
    assert (
        metric_value("content_ingestion_runs_total", {"outcome": "succeeded"})
        == runs_before + 1
    )
    assert metric_value("content_ingestion_articles_created_total") == articles_before + 2
    assert metric_value("content_ingestion_failures_total") == failures_before
    assert (
        started_at
        <= metric_value("content_ingestion_last_completion_timestamp_seconds")
        <= time.time()
    )


def test_returns_201_when_ingestion_partially_succeeds(
    client: TestClient,
    synchronize_sources: Mock,
) -> None:
    synchronize_sources.execute.return_value = SynchronizationResult(
        articles_created=2,
        failures=3,
        sources_succeeded=1,
        sources_failed=1,
    )
    runs_before = metric_value("content_ingestion_runs_total", {"outcome": "partial"})
    articles_before = metric_value("content_ingestion_articles_created_total")
    failures_before = metric_value("content_ingestion_failures_total")
    started_at = time.time()

    response: Response = client.post(routes.INGESTION_RUNS)

    assert response.status_code == 201
    assert response.json() == {"status": "partial"}
    assert (
        metric_value("content_ingestion_runs_total", {"outcome": "partial"})
        == runs_before + 1
    )
    assert metric_value("content_ingestion_articles_created_total") == articles_before + 2
    assert metric_value("content_ingestion_failures_total") == failures_before + 3
    assert (
        started_at
        <= metric_value("content_ingestion_last_completion_timestamp_seconds")
        <= time.time()
    )


def test_returns_structured_502_when_ingestion_fails(
    client: TestClient,
    synchronize_sources: Mock,
) -> None:
    synchronize_sources.execute.return_value = SynchronizationResult(
        failures=2,
        sources_failed=1,
    )
    runs_before = metric_value("content_ingestion_runs_total", {"outcome": "failed"})
    articles_before = metric_value("content_ingestion_articles_created_total")
    failures_before = metric_value("content_ingestion_failures_total")
    started_at = time.time()

    response: Response = client.post(routes.INGESTION_RUNS)

    assert response.status_code == 502
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "ARTICLE_INGESTION_FAILED"
    assert body.error.message == "Article ingestion completed with errors."
    assert (
        metric_value("content_ingestion_runs_total", {"outcome": "failed"})
        == runs_before + 1
    )
    assert metric_value("content_ingestion_articles_created_total") == articles_before
    assert metric_value("content_ingestion_failures_total") == failures_before + 2
    assert (
        started_at
        <= metric_value("content_ingestion_last_completion_timestamp_seconds")
        <= time.time()
    )


def test_records_unexpected_failure_without_changing_exception_behavior(
    client: TestClient,
    synchronize_sources: Mock,
) -> None:
    synchronize_sources.execute.side_effect = RuntimeError("unexpected failure")
    runs_before = metric_value("content_ingestion_runs_total", {"outcome": "failed"})
    articles_before = metric_value("content_ingestion_articles_created_total")
    failures_before = metric_value("content_ingestion_failures_total")
    started_at = time.time()

    with pytest.raises(RuntimeError, match="unexpected failure"):
        client.post(routes.INGESTION_RUNS)

    assert (
        metric_value("content_ingestion_runs_total", {"outcome": "failed"})
        == runs_before + 1
    )
    assert metric_value("content_ingestion_articles_created_total") == articles_before
    assert metric_value("content_ingestion_failures_total") == failures_before
    assert (
        started_at
        <= metric_value("content_ingestion_last_completion_timestamp_seconds")
        <= time.time()
    )


def test_returns_409_when_an_ingestion_is_already_running(
    client: TestClient,
    synchronize_sources: Mock,
) -> None:
    synchronize_sources.execute.side_effect = ArticleIngestionAlreadyRunningError()
    runs_before = {
        outcome: metric_value("content_ingestion_runs_total", {"outcome": outcome})
        for outcome in ("succeeded", "partial", "failed")
    }
    completion_before = metric_value(
        "content_ingestion_last_completion_timestamp_seconds"
    )

    response: Response = client.post(routes.INGESTION_RUNS)

    assert response.status_code == 409
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "ARTICLE_INGESTION_ALREADY_RUNNING"
    assert all(
        metric_value("content_ingestion_runs_total", {"outcome": outcome}) == count
        for outcome, count in runs_before.items()
    )
    assert (
        metric_value("content_ingestion_last_completion_timestamp_seconds")
        == completion_before
    )


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
