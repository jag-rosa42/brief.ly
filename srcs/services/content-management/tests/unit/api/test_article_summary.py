from collections.abc import Generator
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from shared_errors import ErrorResponse

from src.api.dependencies.article import get_update_article_summary
from src.domain.entities import ArticleSummary, NormalizedArticle
from src.domain.exception import ArticleNotFoundError
from src.main import app
from tests import routes


@pytest.fixture
def client(service_headers: dict[str, str]) -> TestClient:
    return TestClient(app, headers=service_headers)


@pytest.fixture
def update_article_summary() -> Generator[Mock]:
    use_case = Mock()
    app.dependency_overrides[get_update_article_summary] = lambda: use_case
    yield use_case
    app.dependency_overrides.pop(get_update_article_summary, None)


def test_updates_an_article_summary(
    client: TestClient,
    update_article_summary: Mock,
    normalized_article: NormalizedArticle,
) -> None:
    summarized_at = datetime(2026, 11, 3, 10, 30, tzinfo=UTC)
    summarized = replace(
        normalized_article,
        summary=ArticleSummary(
            text="Useful summary",
            summarized_at=summarized_at,
            llm_model="test-model",
            rejected=False,
            quality_comment="Looks good",
            generation_duration_ms=1200,
        ),
    )
    update_article_summary.execute.return_value = summarized

    response = client.put(
        routes.article_summary(normalized_article.id),
        json={
            "text": "Useful summary",
            "llm_model": "test-model",
            "rejected": False,
            "quality_comment": "Looks good",
            "generation_duration_ms": 1200,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "article_id": str(normalized_article.id),
        "title": normalized_article.title,
        "publisher_name": normalized_article.publisher_name,
        "url": normalized_article.url,
        "topic_id": normalized_article.category,
        "language": normalized_article.language,
        "content": normalized_article.content,
        "read_time_minutes": 1,
        "summary": "Useful summary",
        "summarized_at": summarized_at.isoformat().replace("+00:00", "Z"),
        "rejected": False,
        "quality_comment": "Looks good",
        "generation_duration_ms": 1200,
    }
    update_article_summary.execute.assert_called_once_with(
        article_id=normalized_article.id,
        text="Useful summary",
        llm_model="test-model",
        rejected=False,
        quality_comment="Looks good",
        generation_duration_ms=1200,
    )


def test_accepts_a_null_summary_for_a_rejected_article(
    client: TestClient,
    update_article_summary: Mock,
    normalized_article: NormalizedArticle,
) -> None:
    rejected_article = replace(
        normalized_article,
        summary=ArticleSummary(
            text=None,
            summarized_at=datetime(2026, 11, 3, 10, 30, tzinfo=UTC),
            llm_model="test-model",
            rejected=True,
            quality_comment="Irrelevant article",
            generation_duration_ms=1200,
        ),
    )
    update_article_summary.execute.return_value = rejected_article

    response = client.put(
        routes.article_summary(normalized_article.id),
        json={
            "text": None,
            "llm_model": "test-model",
            "rejected": True,
            "quality_comment": "Irrelevant article",
            "generation_duration_ms": 1200,
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"] is None
    assert response.json()["language"] == normalized_article.language
    update_article_summary.execute.assert_called_once_with(
        article_id=normalized_article.id,
        text=None,
        llm_model="test-model",
        rejected=True,
        quality_comment="Irrelevant article",
        generation_duration_ms=1200,
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": "", "llm_model": "test-model"},
        {"text": "   ", "llm_model": "test-model"},
        {
            "text": "",
            "llm_model": "test-model",
            "rejected": False,
            "quality_comment": "Looks good",
            "generation_duration_ms": 1200,
        },
        {
            "text": None,
            "llm_model": "test-model",
            "rejected": False,
            "quality_comment": "Looks good",
            "generation_duration_ms": 1200,
        },
        {
            "text": "Summary",
            "llm_model": "test-model",
            "rejected": True,
            "quality_comment": "Irrelevant article",
            "generation_duration_ms": 1200,
        },
        {
            "text": "",
            "llm_model": "test-model",
            "rejected": True,
            "quality_comment": "Irrelevant article",
            "generation_duration_ms": 1200,
        },
        {"text": "a" * 2001, "llm_model": "test-model"},
        {"text": "Summary", "llm_model": ""},
        {
            "text": "Summary",
            "llm_model": "test-model",
            "rejected": False,
            "quality_comment": "Looks good",
            "generation_duration_ms": 1200,
            "extra": True,
        },
        {
            "text": "Summary",
            "llm_model": "test-model",
            "rejected": False,
            "quality_comment": "Looks good",
            "generation_duration_ms": -1,
        },
    ],
)
def test_rejects_invalid_payloads(
    client: TestClient,
    update_article_summary: Mock,
    normalized_article: NormalizedArticle,
    payload: dict,
) -> None:
    response = client.put(routes.article_summary(normalized_article.id), json=payload)

    assert response.status_code == 422
    assert ErrorResponse.model_validate(response.json()).error.code == "VALIDATION_ERROR"
    update_article_summary.execute.assert_not_called()


def test_returns_article_not_found(
    client: TestClient,
    update_article_summary: Mock,
    normalized_article: NormalizedArticle,
) -> None:
    update_article_summary.execute.side_effect = ArticleNotFoundError()

    response = client.put(
        routes.article_summary(normalized_article.id),
        json={
            "text": "Summary",
            "llm_model": "test-model",
            "rejected": False,
            "quality_comment": "Looks good",
            "generation_duration_ms": 1200,
        },
    )

    assert response.status_code == 404
    body = ErrorResponse.model_validate(response.json())
    assert body.error.code == "ARTICLE_NOT_FOUND"


def test_rejects_an_invalid_article_identifier(
    client: TestClient,
    update_article_summary: Mock,
) -> None:
    response = client.put(
        "/internal/v1/articles/not-a-uuid/summary",
        json={
            "text": "Summary",
            "llm_model": "test-model",
            "rejected": False,
            "quality_comment": "Looks good",
            "generation_duration_ms": 1200,
        },
    )

    assert response.status_code == 422
    assert ErrorResponse.model_validate(response.json()).error.code == "VALIDATION_ERROR"
    update_article_summary.execute.assert_not_called()


def test_exposes_the_summary_put_operation() -> None:
    summary_path = app.openapi()["paths"][routes.ARTICLE_SUMMARY]

    assert set(summary_path) == {"put"}
    responses = summary_path["put"]["responses"]
    assert {"200", "404", "422", "500"} <= set(responses)
