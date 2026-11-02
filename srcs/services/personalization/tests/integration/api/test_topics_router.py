from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2._models import Response
from shared_errors import ErrorResponse

from src.api.dependencies import ACCOUNT_ID_HEADER_NAME
from src.api.dependencies.topic_catalog import get_topic_catalog
from src.main import app
from tests.fakes import FakeTopicCatalog
from tests.routes import TOPICS

CATALOG = ["science", "sports", "health", "business"]


@pytest.fixture
def topic_catalog(client: TestClient) -> FakeTopicCatalog:
    catalog = FakeTopicCatalog(CATALOG)
    app.dependency_overrides[get_topic_catalog] = lambda: catalog
    return catalog


def _headers() -> dict[str, str]:
    return {ACCOUNT_ID_HEADER_NAME: str(uuid4())}


def test_get_returns_the_topics_sorted_by_id(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    response = client.get(
        TOPICS,
        headers=_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "items": [
            {"id": "business"},
            {"id": "health"},
            {"id": "science"},
            {"id": "sports"},
        ]
    }


def test_get_returns_401_without_the_account_header(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    response = client.get(
        TOPICS,
    )

    assert response.status_code == 401
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "INVALID_ACCOUNT_ID"


def test_get_returns_503_when_the_catalog_is_unavailable(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    headers = _headers()
    app.dependency_overrides[get_topic_catalog] = lambda: FakeTopicCatalog(
        CATALOG, available=False
    )

    response: Response = client.get(
        TOPICS,
        headers=headers,
    )

    assert response.status_code == 503
    assert (
        ErrorResponse.model_validate(response.json()).error.code == "SERVICE_UNAVAILABLE"
    )
