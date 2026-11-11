import json
from contextlib import closing
from uuid import UUID

import httpx2 as httpx
import pytest
from shared_auth import DownstreamClient, DownstreamError
from shared_errors import InfrastructureError

from src.domain.value_objects.article_assessment import ArticleAssessment
from src.infrastructure.clients.ContentManagementClient import ContentManagementClient
from tests.fakes import FakeServiceTokenProvider
from tests.model import DEFAULT_MODEL


def _client(transport: httpx.MockTransport) -> closing[DownstreamClient]:
    """A DownstreamClient whose calls are answered by `transport`."""
    return closing(
        DownstreamClient(
            "content-management", "http://content-management", transport=transport
        )
    )


def test_requests_send_the_service_token() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer service-token"
        return httpx.Response(200, json={"items": []})

    with _client(httpx.MockTransport(respond)) as http_client:
        client = ContentManagementClient(http_client, FakeServiceTokenProvider())
        assert client.list_missing_articles(limit=25) == []


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

    with _client(httpx.MockTransport(respond)) as http_client:
        client = ContentManagementClient(http_client, FakeServiceTokenProvider())
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
        assert request.headers["Authorization"] == "Bearer service-token"
        assert json.loads(request.content) == {
            "text": "A concise summary.",
            "rejected": False,
            "quality_comment": "Complete article",
            "llm_model": DEFAULT_MODEL,
            "generation_duration_ms": 1234,
        }
        return httpx.Response(200, json={"article_id": str(article_id)})

    with _client(httpx.MockTransport(respond)) as http_client:
        client = ContentManagementClient(http_client, FakeServiceTokenProvider())
        client.save_article_assessment(
            article_id,
            ArticleAssessment(False, "Complete article", "A concise summary.", 1234),
            DEFAULT_MODEL,
        )


def test_save_article_assessment_reports_unavailable_service() -> None:
    article_id = UUID("123e4567-e89b-12d3-a456-426614174000")

    with _client(httpx.MockTransport(lambda request: httpx.Response(503))) as http_client:
        client = ContentManagementClient(http_client, FakeServiceTokenProvider())
        with pytest.raises(InfrastructureError):
            client.save_article_assessment(
                article_id,
                ArticleAssessment(False, "Complete article", "A concise summary.", 1234),
                DEFAULT_MODEL,
            )


def test_list_missing_articles_reports_connection_failure() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with _client(httpx.MockTransport(fail)) as http_client:
        client = ContentManagementClient(http_client, FakeServiceTokenProvider())
        with pytest.raises(InfrastructureError):
            client.list_missing_articles(limit=25)


def test_save_article_assessment_preserves_non_availability_error() -> None:
    article_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    with _client(httpx.MockTransport(lambda request: httpx.Response(404))) as http_client:
        client = ContentManagementClient(http_client, FakeServiceTokenProvider())
        with pytest.raises(DownstreamError):
            client.save_article_assessment(
                article_id,
                ArticleAssessment(False, "Complete article", "A summary.", 1234),
                DEFAULT_MODEL,
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
            "llm_model": DEFAULT_MODEL,
            "generation_duration_ms": 1234,
        }
        return httpx.Response(200)

    with _client(httpx.MockTransport(respond)) as http_client:
        client = ContentManagementClient(http_client, FakeServiceTokenProvider())
        client.save_article_assessment(
            article_id,
            ArticleAssessment(True, "Article is incomplete", None, 1234),
            DEFAULT_MODEL,
        )


def test_topic_read_uses_existing_response_and_write_uses_contract_body() -> None:
    article_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    calls: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer service-token"
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
            "llm_model": DEFAULT_MODEL,
            "generation_duration_ms": 123,
        }
        return httpx.Response(200)

    with _client(httpx.MockTransport(respond)) as http_client:
        client = ContentManagementClient(http_client, FakeServiceTokenProvider())
        assert client.list_topics() == ["technology"]
        articles = client.list_topic_article_summaries("technology", 25)
        client.save_topic_summary(
            "technology", "Combined topic summary", DEFAULT_MODEL, 123
        )

    assert [(item.article_id, item.summary) for item in articles] == [
        (article_id, "Stored summary")
    ]
    assert calls == ["topics", "articles", "put"]


@pytest.mark.parametrize(
    ("error", "message"),
    [
        pytest.param(
            InfrastructureError("Identity is unavailable."),
            "Identity is unavailable",
            id="identity-unreachable",
        ),
        pytest.param(
            DownstreamError(service="identity", status_code=401, code="INVALID_CLIENT"),
            r"Identity refused AI Processing's credentials \(INVALID_CLIENT\)",
            id="identity-refuses",
        ),
    ],
)
def test_raises_without_calling_content_management_when_no_token(
    error: Exception, message: str
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Content Management must not be called without a token")

    with _client(httpx.MockTransport(respond)) as http_client:
        client = ContentManagementClient(
            http_client, FakeServiceTokenProvider(error=error)
        )
        with pytest.raises(InfrastructureError, match=message):
            client.list_topics()


def test_raises_unavailable_when_our_service_token_expired() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"code": "TOKEN_EXPIRED"}})

    with _client(httpx.MockTransport(respond)) as http_client:
        client = ContentManagementClient(http_client, FakeServiceTokenProvider())
        with pytest.raises(InfrastructureError):
            client.list_topics()
