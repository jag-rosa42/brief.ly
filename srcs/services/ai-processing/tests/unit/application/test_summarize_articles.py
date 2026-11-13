from uuid import UUID

import pytest

from src.application.models.answer_validation_error import AnswerValidationError
from src.application.models.article import Article
from src.application.summarize_articles_and_topics import SummarizeArticlesAndTopics
from src.application.SummarizeArticles import (
    ARTICLE_GENERATION_MAX_ATTEMPTS,
    SummarizeArticles,
)
from src.domain.value_objects.article_assessment import ArticleAssessment
from tests.model import DEFAULT_MODEL, RecordingFailureMetrics


def make_article(article_id: str) -> Article:
    return Article(
        id=UUID(article_id),
        title="Example",
        content="Full article text",
        language="en",
        topic_id="technology",
    )


@pytest.mark.parametrize("save_fails", [False, True])
def test_exhausted_retries_allow_later_batches_and_topics_unless_save_fails(
    save_fails: bool,
) -> None:
    failed = make_article("123e4567-e89b-12d3-a456-426614174001")
    later = make_article("123e4567-e89b-12d3-a456-426614174002")
    saved: list[tuple[UUID, ArticleAssessment]] = []
    calls: list[UUID] = []
    topics_run: list[bool] = []

    class ContentManagement:
        def __init__(self) -> None:
            self.batches = [[failed], [later], []]

        def list_missing_articles(self, limit: int) -> list[Article]:
            return self.batches.pop(0)

        def save_article_assessment(
            self, article_id: UUID, assessment: ArticleAssessment, llm_model: str
        ) -> None:
            if save_fails:
                raise RuntimeError("save rejected assessment failed")
            saved.append((article_id, assessment))

    class Summarizer:
        def ai_summarize_article(
            self,
            article: Article,
            *,
            previous_failure: AnswerValidationError | None = None,
        ) -> ArticleAssessment:
            calls.append(article.id)
            if article.id == failed.id:
                raise ValueError("Ollama stopped generating a decision: length")
            return ArticleAssessment(False, "Complete article", "Complete summary.", 12)

    class Topics:
        def execute(self) -> None:
            topics_run.append(True)

    metrics = RecordingFailureMetrics()
    workflow = SummarizeArticlesAndTopics(
        SummarizeArticles(ContentManagement(), Summarizer(), DEFAULT_MODEL, 25, metrics),
        Topics(),
    )
    if save_fails:
        with pytest.raises(RuntimeError, match="save rejected assessment failed"):
            workflow.execute()
        assert not saved
        assert not topics_run
        assert calls == [failed.id] * 4
    else:
        workflow.execute()
        assert calls == [failed.id] * 4 + [later.id]
        assert [article_id for article_id, _ in saved] == [failed.id, later.id]
        assert saved[0][1].rejected is True
        assert saved[0][1].summary is None
        assert saved[1][1].rejected is False
        assert topics_run == [True]
    assert metrics.article_failures == 4


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
        def ai_summarize_article(
            self,
            article: Article,
            *,
            previous_failure: AnswerValidationError | None = None,
        ) -> ArticleAssessment:
            return ArticleAssessment(
                False, "Complete article", f"Summary of {article.id}", 1234
            )

    content_management = ContentManagement()
    metrics = RecordingFailureMetrics()
    SummarizeArticles(
        content_management,
        Summarizer(),
        DEFAULT_MODEL,
        batch_size=25,
        failure_metrics=metrics,
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
    assert metrics.article_failures == 0


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
        def ai_summarize_article(
            self,
            article: Article,
            *,
            previous_failure: AnswerValidationError | None = None,
        ) -> ArticleAssessment:
            return ArticleAssessment(False, "Complete article", "Summary", 1234)

    content_management = ContentManagement()
    metrics = RecordingFailureMetrics()
    with pytest.raises(RuntimeError, match="write failed"):
        SummarizeArticles(
            content_management,
            Summarizer(),
            DEFAULT_MODEL,
            batch_size=25,
            failure_metrics=metrics,
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
        def ai_summarize_article(
            self,
            article: Article,
            *,
            previous_failure: AnswerValidationError | None = None,
        ) -> ArticleAssessment:
            return ArticleAssessment(True, "Article is incomplete", None, 1234)

    content_management = ContentManagement()
    metrics = RecordingFailureMetrics()
    SummarizeArticles(
        content_management,
        Summarizer(),
        DEFAULT_MODEL,
        batch_size=25,
        failure_metrics=metrics,
    ).execute()

    assert content_management.saved == [
        (
            article.id,
            ArticleAssessment(True, "Article is incomplete", None, 1234),
            DEFAULT_MODEL,
        )
    ]
    assert content_management.fetch_count == 2
    assert metrics.article_failures == 0


@pytest.mark.parametrize(
    "failure", [RuntimeError("Ollama unavailable"), ValueError("invalid summary")]
)
@pytest.mark.parametrize("failures_before_result", [1, 3, 4])
@pytest.mark.parametrize("quality_rejected", [False, True])
def test_generation_failures_retry_only_failed_articles(
    failure: Exception, failures_before_result: int, quality_rejected: bool
) -> None:
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

    calls: list[UUID] = []

    class Summarizer:
        def ai_summarize_article(
            self,
            article: Article,
            *,
            previous_failure: AnswerValidationError | None = None,
        ) -> ArticleAssessment:
            calls.append(article.id)
            if article.id == failed.id:
                if calls.count(failed.id) <= failures_before_result:
                    raise failure
                if quality_rejected:
                    return ArticleAssessment(True, "Incomplete article", None, 12)
            return ArticleAssessment(False, "Complete article", "Summary", 12)

    content_management = ContentManagement()
    metrics = RecordingFailureMetrics()
    use_case = SummarizeArticles(
        content_management,
        Summarizer(),
        DEFAULT_MODEL,
        batch_size=25,
        failure_metrics=metrics,
    )
    use_case.execute()
    assert content_management.fetch_count == 2
    assert [item[0] for item in content_management.saved] == [accepted.id, failed.id]
    assessment = content_management.saved[1][1]
    if failures_before_result == ARTICLE_GENERATION_MAX_ATTEMPTS:
        assert assessment.rejected is True
        assert assessment.summary is None
        assert assessment.quality_comment == "AI assessment failed after 4 attempts."
        assert assessment.generation_duration_ms >= 0
    else:
        assert assessment.rejected is quality_rejected
        assert assessment.summary == (None if quality_rejected else "Summary")

    assert calls.count(accepted.id) == 1
    assert calls.count(failed.id) == min(failures_before_result + 1, 4)
    assert metrics.article_failures == failures_before_result
