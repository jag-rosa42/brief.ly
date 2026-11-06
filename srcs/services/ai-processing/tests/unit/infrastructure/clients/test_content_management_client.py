import json
from uuid import UUID

import httpx2 as httpx
import pytest

from src.application.models.article_assessment import ArticleAssessment
from src.infrastructure.clients.ContentManagementClient import ContentManagementClient


def test_list_missing_articles_map_response() -> None:
    article_id = "123e4567-e89b-12d3-a456-426614174000"

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/internal/v1/articles"
        assert request.url.params["summary"] == "missing"
        assert request.url.params["limit"] == "25"
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "article_id": article_id,
                        "title": "Example article",
                        "content": "The full article text",
                        "language": "en",
                        "topic_id": "technology",
                    }
                ]
            },
        )

    with httpx.Client(
        base_url="http://content-management", transport=httpx.MockTransport(respond)
    ) as http_client:
        client = ContentManagementClient(http_client)
        articles = client.list_missing_articles(limit=25)

    assert len(articles) == 1
    assert articles[0].id == UUID(article_id)
    assert articles[0].content == "The full article text"
    assert articles[0].language == "en"


def test_save_article_assessment_sends_expected_put() -> None:
    article_id = UUID("123e4567-e89b-12d3-a456-426614174000")

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert request.url.path == f"/internal/v1/articles/{article_id}/summary"
        assert "Authorization" not in request.headers
        assert json.loads(request.content) == {
            "text": "A concise summary.",
            "rejected": False,
            "quality_comment": "Complete article",
            "llm_model": "gemma3:1b",
            "generation_duration_ms": 1234,
        }
        return httpx.Response(200, json={"article_id": str(article_id)})

    with httpx.Client(
        base_url="http://content-management", transport=httpx.MockTransport(respond)
    ) as http_client:
        client = ContentManagementClient(http_client)
        client.save_article_assessment(
            article_id,
            ArticleAssessment(False, "Complete article", "A concise summary.", 1234),
            "gemma3:1b",
        )


def test_save_article_assessment_raises_on_failed_put() -> None:
    article_id = UUID("123e4567-e89b-12d3-a456-426614174000")

    with httpx.Client(
        base_url="http://content-management",
        transport=httpx.MockTransport(lambda request: httpx.Response(503)),
    ) as http_client:
        client = ContentManagementClient(http_client)
        with pytest.raises(httpx.HTTPStatusError):
            client.save_article_assessment(
                article_id,
                ArticleAssessment(False, "Complete article", "A concise summary.", 1234),
                "gemma3:1b",
            )


def test_rejected_assessment_uses_same_put_endpoint() -> None:
    article_id = UUID("123e4567-e89b-12d3-a456-426614174000")

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert request.url.path == f"/internal/v1/articles/{article_id}/summary"
        assert json.loads(request.content) == {
            "text": None,
            "rejected": True,
            "quality_comment": "Article is incomplete",
            "llm_model": "gemma3:1b",
            "generation_duration_ms": 1234,
        }
        return httpx.Response(200)

    with httpx.Client(
        base_url="http://content-management", transport=httpx.MockTransport(respond)
    ) as http_client:
        client = ContentManagementClient(http_client)
        client.save_article_assessment(
            article_id,
            ArticleAssessment(True, "Article is incomplete", None, 1234),
            "gemma3:1b",
        )


def test_topic_read_uses_existing_response_and_write_uses_contract_body() -> None:
    article_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        assert "Authorization" not in request.headers
        if request.method == "GET" and request.url.path == "/internal/v1/topics":
            calls.append("topics")
            return httpx.Response(200, json=[{"id": "technology"}])
        if request.method == "GET":
            calls.append("articles")
            assert request.url.path == "/internal/v1/articles"
            assert request.url.params["topic_id"] == "technology"
            assert request.url.params["limit"] == "25"
            assert "cursor" not in request.url.params
            return httpx.Response(
                200,
                json={
                    "items": [
                        {"article_id": str(article_id), "summary": "Stored summary"}
                    ],
                },
            )
        calls.append("put")
        assert request.url.path == "/internal/v1/topics/technology/summary"
        assert json.loads(request.content) == {
            "text": "Combined topic summary",
            "llm_model": "gemma3:1b",
        }
        return httpx.Response(200)

    with httpx.Client(
        base_url="http://content-management", transport=httpx.MockTransport(respond)
    ) as http_client:
        client = ContentManagementClient(http_client)
        assert client.list_topics() == ["technology"]
        articles = client.list_topic_article_summaries("technology", 25)
        client.save_topic_summary("technology", "Combined topic summary", "gemma3:1b")

    assert [(item.article_id, item.summary) for item in articles] == [
        (article_id, "Stored summary")
    ]
    assert calls == ["topics", "articles", "put"]
