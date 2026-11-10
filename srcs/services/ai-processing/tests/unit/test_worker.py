import json
from contextlib import closing
from uuid import UUID

import httpx2 as httpx
import pytest
from prometheus_client import CollectorRegistry, generate_latest
from shared_auth import DownstreamClient

from src.infrastructure.config.worker import WorkerSettings
from src.infrastructure.metrics.worker import (
    PUSHGATEWAY_ADDRESS,
    PUSHGATEWAY_JOB,
    WorkerRunMetrics,
    publish_worker_metrics,
)
from src.worker import run_worker
from tests.fakes import FakeServiceTokenProvider
from tests.model import DEFAULT_MODEL


def test_push_uses_stable_internal_job(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, CollectorRegistry]] = []

    def fake_push(address: str, *, job: str, registry: CollectorRegistry) -> None:
        calls.append((address, job, registry))

    monkeypatch.setattr("src.infrastructure.metrics.worker.push_to_gateway", fake_push)
    registry = WorkerRunMetrics().registry
    publish_worker_metrics(registry)

    assert calls == [(PUSHGATEWAY_ADDRESS, PUSHGATEWAY_JOB, registry)]
    assert PUSHGATEWAY_ADDRESS == "pushgateway:9091"
    assert PUSHGATEWAY_JOB == "ai_processing_summary"


@pytest.mark.parametrize(
    ("failure_kind", "expected_success", "article_failures", "topic_failures"),
    [
        (None, 1, 0, 0),
        ("article", 0, 1, 0),
        ("topic", 0, 0, 1),
        ("fatal", 0, 0, 0),
    ],
)
def test_worker_publishes_last_run_even_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    failure_kind: str | None,
    expected_success: int,
    article_failures: int,
    topic_failures: int,
) -> None:
    class FakeWorkflow:
        def __init__(self, articles, topics) -> None:
            self.articles = articles
            self.topics = topics

        def execute(self) -> None:
            if failure_kind == "article":
                self.articles.failure_metrics.article_generation_failed()
            elif failure_kind == "topic":
                self.topics.failure_metrics.topic_group_generation_failed()
            elif failure_kind == "fatal":
                raise RuntimeError("sensitive exception message")

    monkeypatch.setattr("src.worker.SummarizeArticlesAndTopics", FakeWorkflow)
    published: list[CollectorRegistry] = []
    settings = WorkerSettings(
        _env_file=None,
        OLLAMA_BASE_URL="http://ollama:11434",
        OLLAMA_MODEL=DEFAULT_MODEL,
    )
    with httpx.Client() as client:
        if failure_kind == "fatal":
            with pytest.raises(RuntimeError, match="sensitive exception message"):
                run_worker(
                    settings,
                    client,
                    client,
                    FakeServiceTokenProvider(),
                    publish=published.append,
                )
        else:
            run_worker(
                settings,
                client,
                client,
                FakeServiceTokenProvider(),
                publish=published.append,
            )

    assert len(published) == 1
    registry = published[0]
    assert registry.get_sample_value("ai_worker_last_run_success") == expected_success
    assert (
        registry.get_sample_value("ai_worker_last_run_article_failures")
        == article_failures
    )
    assert (
        registry.get_sample_value("ai_worker_last_run_topic_failures") == topic_failures
    )
    duration = registry.get_sample_value("ai_worker_last_run_duration_seconds")
    completion = registry.get_sample_value("ai_worker_last_completion_timestamp_seconds")
    assert duration is not None and duration >= 0
    assert completion is not None and completion > 0
    samples = [sample for family in registry.collect() for sample in family.samples]
    assert len(samples) == 5
    assert all(sample.labels == {} for sample in samples)
    assert b"sensitive exception message" not in generate_latest(registry)


def test_failed_push_is_logged_without_hiding_worker_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    class FatalWorkflow:
        def __init__(self, articles, topics) -> None:
            pass

        def execute(self) -> None:
            raise RuntimeError("worker failed")

    def failed_push(registry: CollectorRegistry) -> None:
        raise ConnectionError("Pushgateway unavailable")

    monkeypatch.setattr("src.worker.SummarizeArticlesAndTopics", FatalWorkflow)
    settings = WorkerSettings(
        _env_file=None,
        OLLAMA_BASE_URL="http://ollama:11434",
        OLLAMA_MODEL=DEFAULT_MODEL,
    )
    with httpx.Client() as client, pytest.raises(RuntimeError, match="worker failed"):
        run_worker(
            settings, client, client, FakeServiceTokenProvider(), publish=failed_push
        )
    assert "Failed to push AI worker metrics to Pushgateway" in caplog.text


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
        assert request.headers["Authorization"] == "Bearer service-token"
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
        closing(
            DownstreamClient(
                "content-management",
                settings.CONTENT_MANAGEMENT_BASE_URL,
                transport=httpx.MockTransport(content_respond),
            )
        ) as content_client,
        httpx.Client(
            base_url=settings.OLLAMA_BASE_URL,
            transport=httpx.MockTransport(ollama_respond),
        ) as ollama_client,
    ):
        run_worker(
            settings,
            content_client,
            ollama_client,
            FakeServiceTokenProvider(),
            publish=lambda registry: None,
        )

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
