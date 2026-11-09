from uuid import UUID

import pytest

from src.application.models.article import Article
from src.application.SummarizeArticles import (
    GENERATION_FAILURE_COMMENT,
    SummarizeArticles,
)
from src.domain.value_objects.article_assessment import ArticleAssessment
from tests.model import DEFAULT_MODEL


def make_article(article_id: str) -> Article:
    return Article(
        id=UUID(article_id),
        title="Example",
        content="Full article text",
        language="en",
        topic_id="technology",
    )


def test_processes_all_batches_and_stops_on_empty_result() -> None:
    first = make_article("123e4567-e89b-12d3-a456-426614174001")
    second = make_article("123e4567-e89b-12d3-a456-426614174002")

    class ContentManagement:
        def __init__(self) -> None:
            self.pending_batches = [[first], [second], []]
            self.saved: list[tuple[UUID, ArticleAssessment, str]] = []
            self.requested_limits: list[int] = []

        def list_missing_articles(self, limit: int) -> list[Article]:
            self.requested_limits.append(limit)
            assert len(self.saved) == len(self.requested_limits) - 1
            return self.pending_batches.pop(0)

        def save_article_assessment(
            self, article_id: UUID, assessment: ArticleAssessment, llm_model: str
        ) -> None:
            self.saved.append((article_id, assessment, llm_model))

    class Summarizer:
        def ai_summarize_article(self, article: Article) -> ArticleAssessment:
            return ArticleAssessment(
                False, "Complete article", f"Summary of {article.id}", 1234
            )

    content_management = ContentManagement()
    SummarizeArticles(
        content_management, Summarizer(), DEFAULT_MODEL, batch_size=25
    ).execute()

    assert content_management.requested_limits == [25, 25, 25]
    assert content_management.saved == [
        (
            first.id,
            ArticleAssessment(False, "Complete article", f"Summary of {first.id}", 1234),
            DEFAULT_MODEL,
        ),
        (
            second.id,
            ArticleAssessment(False, "Complete article", f"Summary of {second.id}", 1234),
            DEFAULT_MODEL,
        ),
    ]


def test_failed_write_stops_before_fetching_another_batch() -> None:
    article = make_article("123e4567-e89b-12d3-a456-426614174001")

    class ContentManagement:
        def __init__(self) -> None:
            self.fetch_count = 0

        def list_missing_articles(self, limit: int) -> list[Article]:
            self.fetch_count += 1
            return [article]

        def save_article_assessment(
            self, article_id: UUID, assessment: ArticleAssessment, llm_model: str
        ) -> None:
            raise RuntimeError("write failed")

    class Summarizer:
        def ai_summarize_article(self, article: Article) -> ArticleAssessment:
            return ArticleAssessment(False, "Complete article", "Summary", 1234)

    content_management = ContentManagement()
    with pytest.raises(RuntimeError, match="write failed"):
        SummarizeArticles(
            content_management, Summarizer(), DEFAULT_MODEL, batch_size=25
        ).execute()

    assert content_management.fetch_count == 1


def test_rejected_article_is_recorded_without_a_summary() -> None:
    article = make_article("123e4567-e89b-12d3-a456-426614174001")

    class ContentManagement:
        def __init__(self) -> None:
            self.fetch_count = 0
            self.saved: list[tuple[UUID, ArticleAssessment, str]] = []

        def list_missing_articles(self, limit: int) -> list[Article]:
            self.fetch_count += 1
            return [article] if self.fetch_count == 1 else []

        def save_article_assessment(
            self, article_id: UUID, assessment: ArticleAssessment, llm_model: str
        ) -> None:
            self.saved.append((article_id, assessment, llm_model))

    class Summarizer:
        def ai_summarize_article(self, article: Article) -> ArticleAssessment:
            return ArticleAssessment(True, "Article is incomplete", None, 1234)

    content_management = ContentManagement()
    SummarizeArticles(
        content_management, Summarizer(), DEFAULT_MODEL, batch_size=25
    ).execute()

    assert content_management.saved == [
        (
            article.id,
            ArticleAssessment(True, "Article is incomplete", None, 1234),
            DEFAULT_MODEL,
        )
    ]
    assert content_management.fetch_count == 2


@pytest.mark.parametrize(
    "failure", [RuntimeError("Ollama unavailable"), ValueError("invalid summary")]
)
def test_generation_failure_rejects_article_and_continues(failure: Exception) -> None:
    failed = make_article("123e4567-e89b-12d3-a456-426614174001")
    accepted = make_article("123e4567-e89b-12d3-a456-426614174002")

    class ContentManagement:
        def __init__(self) -> None:
            self.fetch_count = 0
            self.saved: list[tuple[UUID, ArticleAssessment, str]] = []

        def list_missing_articles(self, limit: int) -> list[Article]:
            self.fetch_count += 1
            return [failed, accepted] if self.fetch_count == 1 else []

        def save_article_assessment(
            self, article_id: UUID, assessment: ArticleAssessment, llm_model: str
        ) -> None:
            self.saved.append((article_id, assessment, llm_model))

    class Summarizer:
        def ai_summarize_article(self, article: Article) -> ArticleAssessment:
            if article.id == failed.id:
                raise failure
            return ArticleAssessment(False, "Complete article", "Summary", 12)

    content_management = ContentManagement()
    SummarizeArticles(
        content_management, Summarizer(), DEFAULT_MODEL, batch_size=25
    ).execute()

    assert content_management.fetch_count == 2
    assert [item[0] for item in content_management.saved] == [failed.id, accepted.id]
    rejected = content_management.saved[0][1]
    assert rejected.rejected is True
    assert rejected.summary is None
    assert rejected.quality_comment == GENERATION_FAILURE_COMMENT
    assert rejected.generation_duration_ms >= 0
    assert content_management.saved[1][1].summary == "Summary"
