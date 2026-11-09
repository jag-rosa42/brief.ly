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


def test_topics_api_exposes_only_the_collection_get_operation():
    topic_paths = {
        path: path_item
        for path, path_item in app.openapi()["paths"].items()
        if path.startswith(routes.TOPICS)
    }

    assert set(topic_paths) == {routes.TOPICS}
    assert set(topic_paths[routes.TOPICS]) == {"get"}
