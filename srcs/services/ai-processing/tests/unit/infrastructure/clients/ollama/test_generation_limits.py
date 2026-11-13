import json
import logging
from uuid import UUID

import httpx2 as httpx
import pytest
from shared_errors import InfrastructureError

from src.application.models.answer_validation_error import AnswerValidationError
from src.application.models.article import Article
from src.domain.value_objects.article_assessment import ArticleAssessment
from src.infrastructure.clients.ollama.summarizer_client import (
    OllamaSummarizerClient,
    OllamaTopicSummary,
)


def ask(response, previous=None):
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        return response

    with httpx.Client(
        base_url="http://ollama", transport=httpx.MockTransport(respond)
    ) as client:
        result = OllamaSummarizerClient(client, "test", 120)._ask(
            "system",
            "input",
            OllamaTopicSummary,
            answer_name="summary",
            provider_error_name="summary",
            previous_failure=previous,
        )
    return result, requests


def valid_response():
    return httpx.Response(
        200,
        content=json.dumps(
            {
                "message": {"content": '{"summary":"A complete summary."}'},
                "done": True,
                "done_reason": "stop",
            }
        )
        + "\n",
    )


def test_generation_is_bounded():
    result, requests = ask(valid_response())
    assert result.summary == "A complete summary."
    assert requests[0]["options"]["num_predict"] == 512


def test_truncation_preserves_bounded_answer_for_shorter_retry():
    from src.application.models.generation_limit_error import GenerationLimitError

    response = httpx.Response(
        200,
        content=json.dumps(
            {
                "message": {"content": "x" * 3000},
                "done": True,
                "done_reason": "length",
            }
        )
        + "\n",
    )
    with pytest.raises(GenerationLimitError) as caught:
        ask(response)
    assert len(caught.value.previous_answer) == 2000
    _, requests = ask(valid_response(), caught.value)
    assert requests[0]["options"]["num_predict"] == 256


def test_correction_explicitly_addresses_length_and_rejection():
    _, requests = ask(valid_response(), AnswerValidationError("too long", "{}"))
    instruction = requests[0]["messages"][-1]["content"]
    assert "120 characters" in instruction
    assert "If rejected=true, summary must be null" in instruction


def test_exhausted_technical_failure_remains_pending():
    from src.application.SummarizeArticles import SummarizeArticles
    from tests.model import RecordingFailureMetrics
    from tests.unit.infrastructure.clients.ollama.test_summarizer_client import ARTICLE

    class Content:
        def list_missing_articles(self, limit: int) -> list[Article]:
            return [ARTICLE]

        def save_article_assessment(
            self, article_id: UUID, assessment: ArticleAssessment, llm_model: str
        ) -> None:
            pytest.fail("A technical failure must not reject the article")

    class Summarizer:
        calls = 0

        def ai_summarize_article(
            self,
            article: Article,
            *,
            previous_failure: AnswerValidationError | None = None,
        ) -> ArticleAssessment:
            self.calls += 1
            raise InfrastructureError("Unavailable")

    summarizer = Summarizer()
    with pytest.raises(InfrastructureError, match="remain pending"):
        SummarizeArticles(
            Content(), summarizer, "test", 25, RecordingFailureMetrics()
        ).execute()
    assert summarizer.calls == 4


def test_provider_diagnostics_never_expose_raw_error(caplog, monkeypatch):
    logger = logging.getLogger("src.infrastructure.clients.ollama.summarizer_client")
    # Alembic's logging configuration can disable existing application loggers.
    monkeypatch.setattr(logger, "disabled", False)
    caplog.set_level(logging.WARNING, logger=logger.name)
    response = httpx.Response(
        200,
        content=json.dumps(
            {
                "error": "out of memory SECRET_ARTICLE_TEXT",
            }
        )
        + "\n",
    )
    with pytest.raises(InfrastructureError):
        ask(response)
    assert "category=memory" in caplog.text
    assert "SECRET_ARTICLE_TEXT" not in caplog.text


def test_http_500_is_a_technical_failure():
    with pytest.raises(InfrastructureError, match="HTTP request failed"):
        ask(httpx.Response(500, text="private provider details"))
