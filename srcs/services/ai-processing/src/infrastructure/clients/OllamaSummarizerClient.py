import logging
from collections.abc import Iterator
from contextlib import contextmanager
from http import HTTPStatus
from time import perf_counter
from typing import Annotated, TypeVar

import httpx2
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from shared_errors import InfrastructureError

from src.application.models.article import Article
from src.application.summarize_topics import TOPIC_SUMMARY_GROUP_SIZE
from src.domain.value_objects.article_assessment import ArticleAssessment
from src.domain.value_objects.summary import Summary

logger = logging.getLogger(__name__)
SENTENCE_TERMINATORS = (".", "!", "?", "…", "。", "\uff01", "\uff1f")
TRAILING_CLOSERS = '"”\u2019)]'

# Keep prompt limits and local validation in sync with the API contract.
TOPIC_MIN_INPUT_SUMMARIES = 2
# A fixed temperature makes the same article more likely to receive the same decision.
TEMPERATURE = 0
# Ollama or its proxy can fail temporarily with these gateway statuses.
OLLAMA_UNAVAILABLE_STATUSES = frozenset(
    {
        HTTPStatus.BAD_GATEWAY,
        HTTPStatus.SERVICE_UNAVAILABLE,
        HTTPStatus.GATEWAY_TIMEOUT,
    }
)

ARTICLE_SYSTEM_PROMPT = (
    "Decide whether the Content is usable as a news article. "
    "Reject it only when at least one of these conditions is "
    "true: (1) Content is empty, a placeholder, or explicitly "
    "says the article is unavailable or a draft; (2) Content "
    "visibly ends in an unfinished sentence or clause, such "
    "as 'announced a new' or 'voted on Tuesday, but'; "
    "(3) Content has no complete factual claim about the "
    "reported event beyond the Title. The Title alone cannot "
    "make incomplete Content usable. Otherwise accept it. "
    "Brief articles and articles covering several related "
    "facts are usable. Do not reject for writing style, "
    "organization, or lack of a formal conclusion. "
    "If accepted, set rejected to false, summarize the "
    "article's main facts in its original language in 1 to 4 "
    f"sentences and no more than {Summary.MAX_LENGTH} characters, and use "
    f"quality_comment (1 to {ArticleAssessment.MAX_QUALITY_COMMENT_LENGTH} characters) "
    "to state why it "
    "is usable. An accepted article must have a non-null, "
    "non-empty summary. Do not add facts. "
    "Before returning, check that an accepted summary ends with a complete "
    "sentence; rewrite it if it stops mid-sentence. "
    "If rejected, set "
    "rejected to true, name the failed condition in "
    f"quality_comment (1 to {ArticleAssessment.MAX_QUALITY_COMMENT_LENGTH} characters), "
    "and set summary "
    "to null. "
    "Return only a JSON object with exactly these keys: "
    "rejected, quality_comment, summary."
)
ARTICLE_USER_PROMPT_TEMPLATE = (
    "Title: {title}\nContent: {content}\nLanguage: {language}\n"
)

TOPIC_SYSTEM_PROMPT = (
    "Combine the provided summaries into one concise summary "
    "for the topic. Inputs may summarize individual articles "
    "or earlier groups of articles. Preserve the most important "
    "distinct facts, remove repetition, and keep unrelated "
    "events distinct. Use only facts stated in the inputs; do "
    "not invent details or imply that separate reports describe "
    "the same event. Write in their shared language, or English "
    f"if they use different languages. Keep the summary within {Summary.MAX_LENGTH} "
    "characters. Return only a JSON object with the key summary."
)
TOPIC_USER_PROMPT_TEMPLATE = "Topic: {topic_id}\nInput summaries:\n{numbered_summaries}"

SummaryText = Annotated[str, Field(min_length=1, max_length=Summary.MAX_LENGTH)]


class _OllamaAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class OllamaArticleAssessment(_OllamaAnswer):
    rejected: bool
    quality_comment: Annotated[
        str, Field(min_length=1, max_length=ArticleAssessment.MAX_QUALITY_COMMENT_LENGTH)
    ]
    summary: SummaryText | None


class OllamaTopicSummary(_OllamaAnswer):
    summary: SummaryText


class OllamaChatMessage(BaseModel):
    content: str = ""


class OllamaChatChunk(BaseModel):
    """One line of Ollama's streamed /api/chat response."""

    model_config = ConfigDict(extra="ignore")

    message: OllamaChatMessage | None = None
    done: bool = False
    done_reason: str | None = None
    eval_count: int | None = None
    error: str | None = None


AnswerModel = TypeVar("AnswerModel", bound=_OllamaAnswer)


class OllamaSummarizerClient:
    def __init__(self, http_client: httpx2.Client, model: str, timeout_seconds: float):
        self.http_client = http_client
        self.model = model
        self.timeout_seconds = timeout_seconds

    @contextmanager
    def _stream_chat(self, body: dict[str, object]) -> Iterator[httpx2.Response]:
        try:
            with self.http_client.stream(
                "POST", "/api/chat", json=body, timeout=self.timeout_seconds
            ) as response:
                if response.status_code in OLLAMA_UNAVAILABLE_STATUSES:
                    raise InfrastructureError("Ollama is unavailable.")
                response.raise_for_status()
                yield response
        except httpx2.TransportError as exc:
            raise InfrastructureError("Ollama is unavailable.") from exc

    def ai_summarize_article(self, article: Article) -> ArticleAssessment:
        started_at = perf_counter()
        decision = self._ask(
            ARTICLE_SYSTEM_PROMPT,
            self._article_prompt(article),
            OllamaArticleAssessment,
            answer_name="decision",
            provider_error_name="summary",
        )
        if not decision.rejected and not (decision.summary or "").rstrip(
            TRAILING_CLOSERS
        ).endswith(SENTENCE_TERMINATORS):
            raise ValueError("Ollama returned an unfinished article summary")

        return ArticleAssessment(
            rejected=decision.rejected,
            quality_comment=decision.quality_comment,
            summary=decision.summary,
            generation_duration_ms=max(0, round((perf_counter() - started_at) * 1000)),
        )

    def ai_summarize_topic(self, topic_id: str, summaries: list[str]) -> str:
        if not TOPIC_MIN_INPUT_SUMMARIES <= len(summaries) <= TOPIC_SUMMARY_GROUP_SIZE:
            raise ValueError("Topic summarizer needs 2 to 4 input summaries")

        result = self._ask(
            TOPIC_SYSTEM_PROMPT,
            self._topic_prompt(topic_id, summaries),
            OllamaTopicSummary,
            answer_name="topic summary",
            provider_error_name="topic summary",
        )
        return result.summary

    @staticmethod
    def _article_prompt(article: Article) -> str:
        return ARTICLE_USER_PROMPT_TEMPLATE.format(
            title=article.title,
            content=article.content,
            language=article.language,
        )

    @staticmethod
    def _topic_prompt(topic_id: str, summaries: list[str]) -> str:
        numbered_summaries = "\n".join(
            f"{index}. {summary}" for index, summary in enumerate(summaries, start=1)
        )
        return TOPIC_USER_PROMPT_TEMPLATE.format(
            topic_id=topic_id, numbered_summaries=numbered_summaries
        )

    def _ask(
        self,
        system_prompt: str,
        user_prompt: str,
        answer_model: type[AnswerModel],
        *,
        answer_name: str,
        provider_error_name: str,
    ) -> AnswerModel:
        body: dict[str, object] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": True,
            "format": answer_model.model_json_schema(),
            "options": {"temperature": TEMPERATURE},
        }
        answer_text = self._collect_streamed_content(
            body, answer_name=answer_name, provider_error_name=provider_error_name
        )
        try:
            return answer_model.model_validate_json(answer_text)
        except ValidationError as exc:
            raise ValueError(f"Ollama returned an invalid {answer_name}") from exc

    def _collect_streamed_content(
        self,
        body: dict[str, object],
        *,
        answer_name: str,
        provider_error_name: str,
    ) -> str:
        content_chunks: list[str] = []
        finished = False
        done_reason: str | None = None
        eval_count: int | None = None
        with self._stream_chat(body) as response:
            for line in response.iter_lines():
                if not line:
                    continue
                chunk = OllamaChatChunk.model_validate_json(line)
                if chunk.error is not None:
                    raise InfrastructureError(
                        f"Ollama failed while generating a {provider_error_name}"
                    )
                if chunk.message is not None:
                    content_chunks.append(chunk.message.content)
                if chunk.done:
                    finished = True
                    done_reason = chunk.done_reason
                    eval_count = chunk.eval_count
                    break

        answer_text = "".join(content_chunks).strip()
        if finished:
            logger.info(
                "Ollama %s completed: done_reason=%s eval_count=%s",
                answer_name,
                done_reason,
                eval_count,
            )
        if done_reason not in (None, "stop"):
            raise ValueError(f"Ollama stopped generating a {answer_name}: {done_reason}")
        if not finished or not answer_text:
            raise ValueError(f"Ollama returned an incomplete or empty {answer_name}")
        return answer_text
