from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2._models import Response
from shared_errors import ErrorResponse

from src.api.dependencies import ACCOUNT_ID_HEADER_NAME
from src.api.dependencies.topic_catalog import get_topic_catalog
from src.main import app
from tests.fakes import FakeTopicCatalog
from tests.routes import ME_PROFILE

CATALOG = ["business", "health", "science", "sports"]


@pytest.fixture
def topic_catalog(client: TestClient) -> FakeTopicCatalog:
    catalog = FakeTopicCatalog(CATALOG)
    app.dependency_overrides[get_topic_catalog] = lambda: catalog
    return catalog


def _headers() -> dict[str, str]:
    return {ACCOUNT_ID_HEADER_NAME: str(uuid4())}


def test_put_creates_the_profile(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    response = client.put(
        ME_PROFILE,
        headers=_headers(),
        json={"name": "John", "topic_ids": ["science", "business"]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "John"
    assert body["topic_ids"] == ["business", "science"]


def test_put_updates_the_existing_profile(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    headers = _headers()
    client.put(
        ME_PROFILE, headers=headers, json={"name": "John", "topic_ids": ["science"]}
    )

    response = client.put(ME_PROFILE, headers=headers, json={"name": "Jane"})

    assert response.status_code == 200
    assert response.json()["name"] == "Jane"
    assert response.json()["topic_ids"] == ["science"]


def test_put_rejects_empty_body(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    headers = _headers()
    response: Response = client.put(ME_PROFILE, headers=headers, json={})

    assert ErrorResponse.model_validate(response.json()).error.code == "VALIDATION_ERROR"
    assert response.status_code == 422


def test_put_rejects_duplicated_topics(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    headers = _headers()
    response: Response = client.put(
        ME_PROFILE,
        headers=headers,
        json={"name": "John", "topic_ids": ["science", "science"]},
    )

    assert ErrorResponse.model_validate(response.json()).error.code == "VALIDATION_ERROR"
    assert response.status_code == 422


def test_put_requires_topic_ids_to_create(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    headers = _headers()
    response: Response = client.put(
        ME_PROFILE,
        headers=headers,
        json={"name": "John", "topic_ids": None},
    )
    assert response.status_code == 422
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "VALIDATION_ERROR"
    assert body.error.details is not None
    assert body.error.details[0].field == "topic_ids"


def test_put_rejects_unknown_topics(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    headers = _headers()
    response: Response = client.put(
        ME_PROFILE,
        headers=headers,
        json={"name": "John", "topic_ids": ["pseudoscience"]},
    )

    assert response.status_code == 422
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "VALIDATION_ERROR"
    assert body.error.details is not None
    assert body.error.details[0].message == "Unknown topic id: pseudoscience"


def test_put_returns_503_when_catalog_unavailable(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    headers = _headers()
    app.dependency_overrides[get_topic_catalog] = lambda: FakeTopicCatalog(
        CATALOG, available=False
    )

    response: Response = client.put(
        ME_PROFILE,
        headers=headers,
        json={"name": "John", "topic_ids": ["science"]},
    )

    assert response.status_code == 503
    assert (
        ErrorResponse.model_validate(response.json()).error.code == "SERVICE_UNAVAILABLE"
    )


def test_put_returns_401_when_no_account_header(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    response: Response = client.put(
        ME_PROFILE,
        json={"name": "John", "topic_ids": ["science"]},
    )

    assert response.status_code == 401
    assert (
        ErrorResponse.model_validate(response.json()).error.code == "INVALID_ACCOUNT_ID"
    )


def test_put_rejects_unknown_fields(
    client: TestClient, topic_catalog: FakeTopicCatalog
) -> None:
    headers = _headers()
    response: Response = client.put(
        ME_PROFILE,
        headers=headers,
        json={"name": "John", "topic_ids": ["science"], "names": "Jane"},
    )

    assert response.status_code == 422
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "VALIDATION_ERROR"
    assert body.error.details is not None
    assert body.error.details[0].field == "names"
