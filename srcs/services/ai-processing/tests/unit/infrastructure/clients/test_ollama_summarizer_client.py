import json
from unittest.mock import patch
from uuid import UUID

import httpx2 as httpx
import pytest

from src.application.models.article import Article
from src.infrastructure.clients.OllamaSummarizerClient import OllamaSummarizerClient

ARTICLE = Article(
    id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    title="City opens a library",
    content="The city opened a library on Monday.",
    language="en",
    topic_id="local-news",
)


def ollama_line(content: str, done: bool = True) -> bytes:
    return (json.dumps({"message": {"content": content}, "done": done}) + "\n").encode()


def test_summarize_article_joins_streamed_json_chunks() -> None:
    assessment = json.dumps(
        {
            "rejected": False,
            "quality_comment": "Complete readable article",
            "summary": "A new library opened.",
        }
    )

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/chat"
        body = json.loads(request.content)
        assert body["model"] == "gemma3:1b"
        assert body["stream"] is True
        assert body["options"]["temperature"] == 0
        schema = body["format"]
        assert schema["type"] == "object"
        assert set(schema["required"]) == {
            "rejected",
            "quality_comment",
            "summary",
        }
        assert schema["additionalProperties"] is False
        assert schema["properties"]["quality_comment"]["maxLength"] == 500
        assert schema["properties"]["summary"]["anyOf"] == [
            {"type": "string", "minLength": 1, "maxLength": 2000},
            {"type": "null"},
        ]
        system_prompt = body["messages"][0]["content"]
        assert "summarize the article" in system_prompt
        assert "Otherwise accept it" in system_prompt
        assert "1 to 4 sentences" in system_prompt
        assert "no more than 2000 characters" in system_prompt
        assert "City opens a library" in body["messages"][1]["content"]
        assert "The city opened a library on Monday." in body["messages"][1]["content"]
        assert "Language: en" in body["messages"][1]["content"]
        midpoint = len(assessment) // 2
        return httpx.Response(
            200,
            content=(
                ollama_line(assessment[:midpoint], done=False)
                + ollama_line(assessment[midpoint:])
            ),
        )

    with httpx.Client(
        base_url="http://ollama:11434", transport=httpx.MockTransport(respond)
    ) as http_client:
        client = OllamaSummarizerClient(http_client, "gemma3:1b", 120.0)
        with patch(
            "src.infrastructure.clients.OllamaSummarizerClient.perf_counter",
            side_effect=[10.0, 10.123],
        ):
            result = client.ai_summarize_article(ARTICLE)

    assert result.rejected is False
    assert result.quality_comment == "Complete readable article"
    assert result.summary == "A new library opened."
    assert result.generation_duration_ms == 123


def test_summarize_article_can_report_rejection() -> None:
    assessment = json.dumps(
        {
            "rejected": True,
            "quality_comment": "The article text ends mid-sentence",
            "summary": None,
        }
    )
    with httpx.Client(
        base_url="http://ollama:11434",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=ollama_line(assessment))
        ),
    ) as http_client:
        client = OllamaSummarizerClient(http_client, "gemma3:1b", 120.0)
        result = client.ai_summarize_article(ARTICLE)

    assert result.rejected is True
    assert result.quality_comment == "The article text ends mid-sentence"
    assert result.summary is None
    assert result.generation_duration_ms >= 0


@pytest.mark.parametrize(
    "response_content",
    [
        ollama_line("partial", done=False),
        ollama_line("  "),
    ],
)
def test_summarize_article_rejects_incomplete_or_empty_stream(
    response_content: bytes,
) -> None:
    with httpx.Client(
        base_url="http://ollama:11434",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=response_content)
        ),
    ) as http_client:
        client = OllamaSummarizerClient(http_client, "gemma3:1b", 120.0)
        with pytest.raises(ValueError, match="incomplete or empty"):
            client.ai_summarize_article(ARTICLE)


@pytest.mark.parametrize(
    "assessment",
    [
        "bad quality content",
        json.dumps(
            {"rejected": True, "quality_comment": "Incomplete", "summary": "Summary"}
        ),
        json.dumps({"rejected": "yes", "quality_comment": "Incomplete", "summary": None}),
    ],
)
def test_summarize_article_rejects_invalid_assessment(assessment: str) -> None:
    with httpx.Client(
        base_url="http://ollama:11434",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=ollama_line(assessment))
        ),
    ) as http_client:
        client = OllamaSummarizerClient(http_client, "gemma3:1b", 120.0)
        with pytest.raises(ValueError):
            client.ai_summarize_article(ARTICLE)


def test_summarize_article_rejects_streamed_provider_error() -> None:
    with httpx.Client(
        base_url="http://ollama:11434",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=b'{"error":"model failed"}\n')
        ),
    ) as http_client:
        client = OllamaSummarizerClient(http_client, "gemma3:1b", 120.0)
        with pytest.raises(RuntimeError, match="Ollama failed"):
            client.ai_summarize_article(ARTICLE)


