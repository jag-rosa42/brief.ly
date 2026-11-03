from collections.abc import Generator
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_errors import ErrorResponse

from src.api.dependencies.article import get_article_use_case, get_list_articles
from src.api.schemas import ArticleResponse
from src.application.use_cases.articles import GetArticle
from src.domain.entities import NormalizedArticle
from src.domain.exception import ArticleNotFoundError
from src.main import app
from tests import routes


def article_detail_path(article_id: object) -> str:
    return routes.ARTICLE_DETAIL.format(article_id=article_id)


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
def get_article() -> Generator[Mock]:
    use_case = Mock(spec=GetArticle)
    app.dependency_overrides[get_article_use_case] = lambda: use_case
    yield use_case
    app.dependency_overrides.pop(get_article_use_case, None)


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


def test_returns_the_requested_article(
    client: TestClient,
    get_article: Mock,
    normalized_article: NormalizedArticle,
) -> None:
    article = replace(
        normalized_article,
        summary="Article summary",
        summarized_at=datetime(2026, 11, 3, 12, tzinfo=UTC),
    )
    get_article.execute.return_value = article

    response = client.get(article_detail_path(article.id))

    assert response.status_code == 200
    assert response.json() == ArticleResponse.from_domain(article).model_dump(mode="json")
    get_article.execute.assert_called_once_with(article.id)


def test_returns_structured_404_when_the_article_does_not_exist(
    client: TestClient,
    get_article: Mock,
) -> None:
    article_id = uuid4()
    get_article.execute.side_effect = ArticleNotFoundError()

    response = client.get(article_detail_path(article_id))

    assert response.status_code == 404
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "ARTICLE_NOT_FOUND"
    assert body.error.message == "Article not found."


def test_returns_validation_error_for_an_invalid_article_id(
    client: TestClient,
    get_article: Mock,
) -> None:
    response = client.get(article_detail_path("not-a-uuid"))

    assert response.status_code == 422
    assert ErrorResponse.model_validate(response.json()).error.code == "VALIDATION_ERROR"
    get_article.execute.assert_not_called()


def test_exposes_article_collection_and_detail_get_operations() -> None:
    article_paths = {
        path: path_item
        for path, path_item in app.openapi()["paths"].items()
        if path.startswith("/internal/v1/articles")
    }

    assert {routes.ARTICLES, routes.ARTICLE_DETAIL} <= set(article_paths)
    assert set(article_paths[routes.ARTICLES]) == {"get"}
    assert set(article_paths[routes.ARTICLE_DETAIL]) == {"get"}
    responses = article_paths[routes.ARTICLE_DETAIL]["get"]["responses"]
    assert {"200", "404", "422", "500"} <= set(responses)
