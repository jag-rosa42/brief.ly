from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from src.api.dependencies.article import get_list_articles
from src.domain.entities import NormalizedArticle
from src.main import app
from tests import routes


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def list_articles() -> Generator[Mock]:
    use_case = Mock()
    app.dependency_overrides[get_list_articles] = lambda: use_case
    yield use_case
    app.dependency_overrides.pop(get_list_articles, None)


@pytest.fixture
def article() -> NormalizedArticle:
    return NormalizedArticle(
        id=uuid4(),
        discovered_article_external_id="external-id",
        url="https://example.com/article",
        publisher_name="Example source",
        title="Example article",
        description=None,
        content="word " * 201,
        authors=None,
        image_url=None,
        category="science",
        language="en",
        published_at=None,
        summary="Example summary",
        summarized_at=datetime(2026, 11, 3, 10, tzinfo=UTC),
    )


def test_lists_articles_by_topic(
    client: TestClient,
    list_articles: Mock,
    article: NormalizedArticle,
) -> None:
    list_articles.execute.return_value = [article]

    response: Response = client.get(
        routes.ARTICLES,
        params={"topic_id": "science", "limit": 10},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "article_id": str(article.id),
                "title": "Example article",
                "source": "Example source",
                "url": "https://example.com/article",
                "topic_id": "science",
                "read_time_minutes": 1,
                "summary": "Example summary",
                "summarized_at": "2026-11-03T10:00:00Z",
            }
        ]
    }
    list_articles.execute.assert_called_once_with(
        topic_id="science",
        summary_missing=False,
        limit=10,
    )


def test_lists_articles_with_missing_summaries_using_the_default_limit(
    client: TestClient,
    list_articles: Mock,
) -> None:
    list_articles.execute.return_value = []

    response: Response = client.get(routes.ARTICLES, params={"summary": "missing"})

    assert response.status_code == 200
    assert response.json() == {"items": []}
    list_articles.execute.assert_called_once_with(
        topic_id=None,
        summary_missing=True,
        limit=25,
    )


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"topic_id": "science", "summary": "missing"},
        {"summary": "present"},
        {"summary": "missing", "limit": 0},
        {"summary": "missing", "limit": 26},
    ],
)
def test_rejects_invalid_queries(
    client: TestClient,
    list_articles: Mock,
    params: dict[str, str | int],
) -> None:
    response: Response = client.get(routes.ARTICLES, params=params)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    list_articles.execute.assert_not_called()


def test_article_identifier_is_exposed_as_a_uuid(
    article: NormalizedArticle,
) -> None:
    assert isinstance(article.id, UUID)
