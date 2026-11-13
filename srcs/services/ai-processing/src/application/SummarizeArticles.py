import logging
from time import perf_counter
from uuid import UUID

from shared_errors import InfrastructureError

from src.application.models.answer_validation_error import AnswerValidationError
from src.application.models.article import Article
from src.application.models.generation_limit_error import GenerationLimitError
from src.application.ports.ai_summarizer import ArticleSummarizerPort
from src.application.ports.content_management import ArticleContentManagementPort
from src.application.ports.failure_metrics import FailureMetricsPort
from src.domain.value_objects.article_assessment import ArticleAssessment

# The command entry point creates the HTTP clients and passes them to this use case.
logger = logging.getLogger(__name__)
ARTICLE_GENERATION_MAX_ATTEMPTS = 4  # Initial attempt plus three retries.


class SummarizeArticles:
    def __init__(
        self,
        content_management: ArticleContentManagementPort,
        ai_summarizer: ArticleSummarizerPort,
        llm_model: str,
        batch_size: int,
        failure_metrics: FailureMetricsPort,
    ) -> None:
        if batch_size < 1:
            raise ValueError("Article batch size must be positive")
        self.content_management = content_management
        self.ai_summarizer = ai_summarizer
        self.llm_model = llm_model
        self.batch_size = batch_size
        self.failure_metrics = failure_metrics

    def execute(self) -> None:
        while True:
            fetched_at = perf_counter()
            articles: list[Article] = self.content_management.list_missing_articles(
                self.batch_size
            )
            logger.info(
                "Fetched article batch count=%s elapsed=%.2fs",
                len(articles),
                perf_counter() - fetched_at,
            )
            if not articles:
                return

            logger.info("Fetched %s articles awaiting assessment", len(articles))
            pending = articles
            corrections: dict[UUID, AnswerValidationError] = {}
            failed_duration_ms: dict[UUID, int] = {}
            technical_failures: set[UUID] = set()
            for attempt in range(1, ARTICLE_GENERATION_MAX_ATTEMPTS + 1):
                retry_articles: list[Article] = []
                for article in pending:
                    started_at = perf_counter()
                    logger.info(
                        "Starting article assessment for %s (attempt %s/%s)",
                        article.id,
                        attempt,
                        ARTICLE_GENERATION_MAX_ATTEMPTS,
                    )
                    try:
                        if article.id in corrections:
                            assessment = self.ai_summarizer.ai_summarize_article(
                                article, previous_failure=corrections[article.id]
                            )
                        else:
                            assessment = self.ai_summarizer.ai_summarize_article(article)
                    except Exception as exc:
                        failed_duration_ms[article.id] = failed_duration_ms.get(
                            article.id, 0
                        ) + max(0, round((perf_counter() - started_at) * 1000))
                        if isinstance(exc, (InfrastructureError, GenerationLimitError)):
                            technical_failures.add(article.id)
                        else:
                            technical_failures.discard(article.id)
                        if isinstance(exc, AnswerValidationError):
                            corrections[article.id] = exc
                        self.failure_metrics.article_generation_failed()
                        logger.exception(
                            "Article summary generation failed for %s "
                            "(attempt %s/%s) elapsed=%.2fs cumulative_failed=%.2fs",
                            article.id,
                            attempt,
                            ARTICLE_GENERATION_MAX_ATTEMPTS,
                            perf_counter() - started_at,
                            failed_duration_ms[article.id] / 1000,
                        )
                        retry_articles.append(article)
                        continue

                    # A valid quality rejection is final, just like a valid summary.
                    # Failed generations are retried before the fallback rejection below.
                    save_started_at = perf_counter()
                    self.content_management.save_article_assessment(
                        article.id, assessment, self.llm_model
                    )
                    corrections.pop(article.id, None)
                    logger.info(
                        "Saved article assessment for %s: rejected=%s elapsed=%.2fs "
                        "save_elapsed=%.2fs cumulative_failed=%.2fs",
                        article.id,
                        assessment.rejected,
                        perf_counter() - started_at,
                        perf_counter() - save_started_at,
                        failed_duration_ms.get(article.id, 0) / 1000,
                    )
                    if not assessment.rejected and assessment.summary:
                        self.failure_metrics.article_summary_succeeded(
                            max(0, perf_counter() - started_at)
                        )

                pending = retry_articles
                if not pending:
                    break

            deferred_count = 0
            for article in pending:
                if article.id in technical_failures:
                    deferred_count += 1
                    continue
                self.content_management.save_article_assessment(
                    article.id,
                    ArticleAssessment(
                        rejected=True,
                        quality_comment=(
                            "AI assessment failed after "
                            f"{ARTICLE_GENERATION_MAX_ATTEMPTS} attempts."
                        ),
                        summary=None,
                        generation_duration_ms=failed_duration_ms[article.id],
                    ),
                    self.llm_model,
                )
                logger.warning(
                    "Marked article %s rejected after %s failed generation attempts",
                    article.id,
                    ARTICLE_GENERATION_MAX_ATTEMPTS,
                )
            if deferred_count:
                raise InfrastructureError(
                    f"AI assessment deferred for {deferred_count} articles after "
                    f"{ARTICLE_GENERATION_MAX_ATTEMPTS} attempts; "
                    "articles remain pending."
                )
