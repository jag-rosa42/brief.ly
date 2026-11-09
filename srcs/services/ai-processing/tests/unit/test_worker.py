import json
from uuid import UUID

import httpx2 as httpx
import pytest

from src.infrastructure.config.worker import WorkerSettings
from src.worker import run_worker
from tests.model import DEFAULT_MODEL


def test_content_management_defaults_to_compose_service_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CONTENT_MANAGEMENT_BASE_URL", raising=False)
    settings = WorkerSettings(
        _env_file=None,
        OLLAMA_BASE_URL="http://10.0.2.2:11434",
        OLLAMA_MODEL=DEFAULT_MODEL,
    )

    assert settings.CONTENT_MANAGEMENT_BASE_URL == "http://content-management:8000"


def test_worker_wires_get_summarize_put_and_repeats() -> None:
    article_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    calls: list[str] = []
    saved = False

    def content_respond(request: httpx.Request) -> httpx.Response:
        nonlocal saved
        assert "Authorization" not in request.headers
        if request.method == "GET" and request.url.path == "/internal/v1/topics":
            calls.append("topics")
            return httpx.Response(200, json=[{"id": "local-news"}])
        if request.method == "GET" and "topic_id" in request.url.params:
            calls.append("topic_articles")
            assert request.url.params["topic_id"] == "local-news"
            assert request.url.params["limit"] == "25"
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "article_id": str(article_id),
                            "summary": "A new library opened.",
                        },
                        {
                            "article_id": "123e4567-e89b-12d3-a456-426614174001",
                            "summary": "A museum reopened.",
                        },
                    ],
                },
            )
        if request.method == "GET":
            calls.append("get")
            assert request.url.path == "/internal/v1/articles"
            assert request.url.params["summary"] == "missing"
            assert request.url.params["limit"] == "25"
            items = (
                []
                if saved
                else [
                    {
                        "article_id": str(article_id),
                        "title": "City opens a library",
                        "content": "The city opened a library on Monday.",
                        "language": "en",
                        "topic_id": "local-news",
                    }
                ]
            )
            return httpx.Response(200, json={"items": items})

        if request.url.path == "/internal/v1/topics/local-news/summary":
            calls.append("topic_put")
            topic_summary = json.loads(request.content)
            assert topic_summary == {
                "text": "Local venues opened.",
                "llm_model": DEFAULT_MODEL,
                "generation_duration_ms": topic_summary["generation_duration_ms"],
            }
            assert isinstance(topic_summary["generation_duration_ms"], int)
            assert topic_summary["generation_duration_ms"] >= 0
            return httpx.Response(200)

        calls.append("put")
        assert request.method == "PUT"
        assert request.url.path == f"/internal/v1/articles/{article_id}/summary"
        assessment = json.loads(request.content)
        assert assessment == {
            "text": "A new library opened.",
            "rejected": False,
            "quality_comment": "Complete readable article",
            "llm_model": DEFAULT_MODEL,
            "generation_duration_ms": assessment["generation_duration_ms"],
        }
        assert isinstance(assessment["generation_duration_ms"], int)
        assert assessment["generation_duration_ms"] >= 0
        saved = True
        return httpx.Response(200, json={"article_id": str(article_id)})

    def ollama_respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        body = json.loads(request.content)
        assert body["model"] == DEFAULT_MODEL
        if "quality_comment" not in body["format"]["properties"]:
            assert body["stream"] is True
            calls.append("topic_summarize")
            return httpx.Response(
                200,
                content=(
                    json.dumps(
                        {
                            "message": {
                                "content": json.dumps({"summary": "Local venues opened."})
                            },
                            "done": True,
                        }
                    )
                    + "\n"
                ).encode(),
            )

        calls.append("summarize")
        assessment = json.dumps(
            {
                "rejected": False,
                "quality_comment": "Complete readable article",
                "summary": "A new library opened.",
            }
        )
        return httpx.Response(
            200,
            content=(
                json.dumps({"message": {"content": assessment}, "done": True}) + "\n"
            ).encode(),
        )

    settings = WorkerSettings(
        _env_file=None,
        CONTENT_MANAGEMENT_BASE_URL="http://content-management:8000",
        OLLAMA_BASE_URL="http://ollama:11434",
        OLLAMA_MODEL=DEFAULT_MODEL,
    )
    with (
        httpx.Client(
            base_url=settings.CONTENT_MANAGEMENT_BASE_URL,
            transport=httpx.MockTransport(content_respond),
        ) as content_client,
        httpx.Client(
            base_url=settings.OLLAMA_BASE_URL,
            transport=httpx.MockTransport(ollama_respond),
        ) as ollama_client,
    ):
        run_worker(settings, content_client, ollama_client)

    assert calls == [
        "get",
        "summarize",
        "put",
        "get",
        "topics",
        "topic_articles",
        "topic_summarize",
        "topic_put",
    ]
