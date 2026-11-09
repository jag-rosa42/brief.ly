from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from shared_errors import ErrorResponse

from src.api.dependencies.topic import get_update_topic_summary
from src.domain.entities import Topic, TopicSummary
from src.domain.exception import TopicNotFoundError
from src.main import app
from tests import routes


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def update_topic_summary() -> Generator[Mock]:
    use_case = Mock()
    app.dependency_overrides[get_update_topic_summary] = lambda: use_case
    yield use_case
    app.dependency_overrides.pop(get_update_topic_summary, None)


def test_returns_topic_with_summary_and_passes_duration_to_use_case(
    client: TestClient, update_topic_summary: Mock
) -> None:
    summarized_at = datetime(2026, 11, 9, 10, tzinfo=UTC)
    update_topic_summary.execute.return_value = Topic(
        id="science",
        summary=TopicSummary(
            text="Science summary",
            summarized_at=summarized_at,
            llm_model="private-model",
            generation_duration_ms=750,
        ),
    )

    response = client.put(
        routes.topic_summary("science"),
        json={
            "text": " Science summary ",
            "llm_model": " private-model ",
            "generation_duration_ms": 750,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "science",
        "summary": "Science summary",
        "summarized_at": "2026-11-09T10:00:00Z",
    }
    update_topic_summary.execute.assert_called_once_with(
        topic_id="science",
        text="Science summary",
        llm_model="private-model",
        generation_duration_ms=750,
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": "", "llm_model": "model", "generation_duration_ms": 1},
        {"text": "   ", "llm_model": "model", "generation_duration_ms": 1},
        {"text": None, "llm_model": "model", "generation_duration_ms": 1},
        {"text": "x" * 2001, "llm_model": "model", "generation_duration_ms": 1},
        {"text": "Summary", "llm_model": "", "generation_duration_ms": 1},
        {"text": "Summary", "llm_model": "   ", "generation_duration_ms": 1},
        {"text": "Summary", "llm_model": "model", "generation_duration_ms": -1},
        {"text": "Summary", "llm_model": "model"},
        {
            "text": "Summary",
            "llm_model": "model",
            "generation_duration_ms": 1,
            "extra": True,
        },
    ],
)
def test_invalid_payload_uses_standard_validation_error(
    client: TestClient, update_topic_summary: Mock, payload: dict
) -> None:
    response = client.put(routes.topic_summary("science"), json=payload)

    assert response.status_code == 422
    assert ErrorResponse.model_validate(response.json()).error.code == "VALIDATION_ERROR"
    update_topic_summary.execute.assert_not_called()


def test_unknown_topic_uses_standard_not_found_error(
    client: TestClient, update_topic_summary: Mock
) -> None:
    update_topic_summary.execute.side_effect = TopicNotFoundError("unknown")

    response = client.put(
        routes.topic_summary("unknown"),
        json={"text": "Summary", "llm_model": "model", "generation_duration_ms": 0},
    )

    assert response.status_code == 404
    assert ErrorResponse.model_validate(response.json()).error.code == "TOPIC_NOT_FOUND"
