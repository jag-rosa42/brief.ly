import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from src.main import app

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
    response: Response = client.get("/internal/v1/topics")

    assert response.status_code == 200

    topics = response.json()
    assert {topic["id"] for topic in topics} == EXPECTED_TOPIC_IDS
    assert all(isinstance(topic["id"], str) for topic in topics)


def test_topics_api_exposes_only_the_collection_get_operation():
    topic_paths = {
        path: path_item
        for path, path_item in app.openapi()["paths"].items()
        if path.startswith("/internal/v1/topics")
    }

    assert set(topic_paths) == {"/internal/v1/topics"}
    assert set(topic_paths["/internal/v1/topics"]) == {"get"}
