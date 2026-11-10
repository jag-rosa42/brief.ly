"""Explicit six-article batch test with real Ollama and fake Content Management."""

import json
from contextlib import closing
from dataclasses import dataclass, field
from time import perf_counter

import httpx2 as httpx
from shared_auth import DownstreamClient

from scripts.try_ollama_workflow import (
    ARTICLE,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_URL,
    StaticTokenProvider,
)
from src.infrastructure.config.worker import WorkerSettings
from src.worker import run_worker

TOPIC_ID = "technology"
BAD_ARTICLES = [
    {
        "article_id": f"123e4567-e89b-12d3-a456-42661417400{index}",
        "title": title,
        "content": content,
        "language": "en",
        "topic_id": TOPIC_ID,
    }
    for index, title, content in [
        (1, "Company announces a new product", "The company announced a new"),
        (2, "Council votes on transport plan", "The council voted on Tuesday, but"),
        (
            3,
            "Researchers publish climate report",
            "Article unavailable after the headline. The report found",
        ),
        (
            4,
            "Local hospital expands services",
            "Draft article. Opening paragraph only: The hospital said it would",
        ),
        (
            5,
            "Museum announces exhibition",
            "This story was cut off during import. The museum will open",
        ),
    ]
]
ARTICLES = [*BAD_ARTICLES, ARTICLE]
ARTICLE_IDS = {article["article_id"] for article in ARTICLES}


@dataclass
class FakeBatchContentManagement:
    assessments: dict[str, dict[str, object]] = field(default_factory=dict)
    missing_pages: list[list[str]] = field(default_factory=list)
    topic_summary: dict[str, object] | None = None

    def respond(self, request: httpx.Request) -> httpx.Response:
        assert "Authorization" not in request.headers
        path = request.url.path

        if request.method == "GET" and path == "/internal/v1/articles":
            if request.url.params.get("summary") == "missing":
                assert request.url.params.get("limit") == "5"
                pending = [
                    article
                    for article in ARTICLES
                    if article["article_id"] not in self.assessments
                ]
                page = pending[:5]
                self.missing_pages.append([article["article_id"] for article in page])
                return httpx.Response(200, json={"items": page})

            assert request.url.params.get("topic_id") == TOPIC_ID
            assert request.url.params.get("limit") == "25"
            assert request.url.params.get("cursor") is None
            items = [
                {"article_id": article_id, "summary": assessment["text"]}
                for article_id, assessment in self.assessments.items()
                if assessment["text"] is not None
            ]
            return httpx.Response(200, json={"items": items})

        if request.method == "PUT" and path.startswith("/internal/v1/articles/"):
            assert path.endswith("/summary")
            article_id = path.split("/")[4]
            assert article_id in ARTICLE_IDS
            assert article_id not in self.assessments
            assessment = json.loads(request.content)
            assert assessment["llm_model"] == DEFAULT_MODEL
            assert isinstance(assessment["generation_duration_ms"], int)
            assert assessment["generation_duration_ms"] >= 0
            self.assessments[article_id] = assessment
            return httpx.Response(200)

        if request.method == "GET" and path == "/internal/v1/topics":
            assert len(self.assessments) == len(ARTICLES)
            return httpx.Response(200, json=[{"id": TOPIC_ID}])

        if request.method == "PUT" and path == (
            f"/internal/v1/topics/{TOPIC_ID}/summary"
        ):
            assert self.topic_summary is None
            self.topic_summary = json.loads(request.content)
            return httpx.Response(200)

        raise AssertionError(
            f"Unexpected Content Management request: {request.method} {path}"
        )


def test_five_incomplete_articles_then_one_complete_article() -> None:
    settings = WorkerSettings(
        _env_file=None,
        CONTENT_MANAGEMENT_BASE_URL="http://content-management",
        OLLAMA_BASE_URL=DEFAULT_OLLAMA_URL,
        OLLAMA_MODEL=DEFAULT_MODEL,
        ARTICLE_BATCH_SIZE=5,
    )
    fake = FakeBatchContentManagement()
    started = perf_counter()
    with (
        closing(
            DownstreamClient(
                "content-management",
                settings.CONTENT_MANAGEMENT_BASE_URL,
                transport=httpx.MockTransport(fake.respond),
            )
        ) as content_client,
        httpx.Client(base_url=settings.OLLAMA_BASE_URL) as ollama_client,
    ):
        run_worker(settings, content_client, ollama_client, StaticTokenProvider())
    elapsed_seconds = perf_counter() - started

    assert fake.missing_pages == [
        [article["article_id"] for article in BAD_ARTICLES],
        [ARTICLE["article_id"]],
        [],
    ]
    assert len(fake.assessments) == 6
    for article in BAD_ARTICLES:
        assessment = fake.assessments[article["article_id"]]
        assert assessment["rejected"] is True, assessment["quality_comment"]
        assert assessment["text"] is None

    accepted = fake.assessments[ARTICLE["article_id"]]
    assert accepted["rejected"] is False, accepted["quality_comment"]
    summary = accepted["text"]
    assert isinstance(summary, str) and summary.strip()
    assert fake.topic_summary is not None
    assert fake.topic_summary["text"] == summary

    print("Rejected articles: 5")
    print(f"Accepted article summary: {summary}")
    print(f"Six-article workflow: {elapsed_seconds:.2f} seconds")
