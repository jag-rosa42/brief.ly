from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.database.models import TopicModel, TopicSummaryModel
from src.main import app
from tests import routes

EXPECTED_TOPIC_IDS = {
    "business",
    "entertainment",
    "general",
    "health",
    "science",
    "sports",
    "technology",
}


@pytest.mark.integration
def test_get_topics_returns_every_fixed_topic(client: TestClient):
    response: Response = client.get(routes.TOPICS)

    assert response.status_code == 200

    topics = response.json()
    assert {topic["id"] for topic in topics} == EXPECTED_TOPIC_IDS
    assert all(isinstance(topic["id"], str) for topic in topics)


@pytest.mark.integration
def test_get_topics_returns_summaries_in_a_raw_array(
    client: TestClient, db_session: Session
):
    summarized_at = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)
    topic_model = db_session.scalar(select(TopicModel).where(TopicModel.id == "science"))
    assert topic_model is not None
    topic_model.summary = TopicSummaryModel(
        topic_id="science",
        text="Science summary",
        summarized_at=summarized_at,
        llm_model="private-model",
    )
    db_session.flush()

    response: Response = client.get(routes.TOPICS)

    assert response.status_code == 200
    topics = response.json()
    assert isinstance(topics, list)
    assert len(topics) == len(EXPECTED_TOPIC_IDS)
    assert {topic["id"] for topic in topics} == EXPECTED_TOPIC_IDS
    by_id = {topic["id"]: topic for topic in topics}
    assert by_id["science"] == {
        "id": "science",
        "summary": "Science summary",
        "summarized_at": "2026-11-03T09:30:00Z",
    }
    assert all(
        topic == {"id": topic_id, "summary": None, "summarized_at": None}
        for topic_id, topic in by_id.items()
        if topic_id != "science"
    )


@pytest.mark.integration
def test_put_topic_summary_creates_and_replaces_latest_summary(
    client: TestClient, db_session: Session
):
    first = client.put(
        routes.topic_summary("science"),
        json={
            "text": "First summary",
            "llm_model": "model-a",
            "generation_duration_ms": 500,
        },
    )
    second = client.put(
        routes.topic_summary("science"),
        json={
            "text": "Updated summary",
            "llm_model": "model-b",
            "generation_duration_ms": 750,
        },
    )

    assert first.status_code == second.status_code == 200
    assert first.json()["summary"] == "First summary"
    assert second.json()["summary"] == "Updated summary"
    assert set(second.json()) == {"id", "summary", "summarized_at"}
    first_time = datetime.fromisoformat(first.json()["summarized_at"])
    second_time = datetime.fromisoformat(second.json()["summarized_at"])
    assert second_time >= first_time
    assert second_time.tzinfo is not None
    db_session.expire_all()
    persisted = db_session.get(TopicSummaryModel, "science")
    assert persisted is not None
    assert persisted.text == "Updated summary"
    assert persisted.llm_model == "model-b"
    assert persisted.generation_duration_ms == 750
    assert db_session.query(TopicSummaryModel).filter_by(topic_id="science").count() == 1
    topics = client.get(routes.TOPICS).json()
    assert next(topic for topic in topics if topic["id"] == "science") == second.json()


@pytest.mark.integration
def test_put_topic_summary_reports_missing_topic_and_invalid_payload(client: TestClient):
    missing = client.put(
        routes.topic_summary("unknown"),
        json={"text": "Summary", "llm_model": "model", "generation_duration_ms": 1},
    )
    invalid = client.put(
        routes.topic_summary("science"),
        json={"text": "", "llm_model": "model", "generation_duration_ms": -1},
    )

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "TOPIC_NOT_FOUND"
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"


def test_topics_api_exposes_collection_get_and_summary_put_operations():
    topic_paths = {
        path: path_item
        for path, path_item in app.openapi()["paths"].items()
        if path.startswith(routes.TOPICS)
    }

    assert set(topic_paths) == {routes.TOPICS, routes.TOPIC_SUMMARY}
    assert set(topic_paths[routes.TOPICS]) == {"get"}
    assert set(topic_paths[routes.TOPIC_SUMMARY]) == {"put"}
    responses = topic_paths[routes.TOPIC_SUMMARY]["put"]["responses"]
    assert {"200", "404", "422", "500"} <= set(responses)
