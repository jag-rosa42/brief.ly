import logging
from time import perf_counter

from src.application.models.article import Article
from src.application.ports.ai_summarizer import ArticleSummarizerPort
from src.application.ports.content_management import ArticleContentManagementPort
from src.application.ports.failure_metrics import FailureMetricsPort
from src.domain.value_objects.article_assessment import ArticleAssessment

# The command entry point creates the HTTP clients and passes them to this use case.
logger = logging.getLogger(__name__)
GENERATION_FAILURE_COMMENT = "Article summary generation failed"


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
            articles: list[Article] = self.content_management.list_missing_articles(
                self.batch_size
            )
            if not articles:
                return

            for article in articles:
                started_at = perf_counter()
                try:
                    assessment = self.ai_summarizer.ai_summarize_article(article)
                except Exception:
                    self.failure_metrics.article_generation_failed()
                    logger.exception(
                        "Article summary generation failed for %s", article.id
                    )
                    assessment = ArticleAssessment(
                        rejected=True,
                        quality_comment=GENERATION_FAILURE_COMMENT,
                        summary=None,
                        generation_duration_ms=max(
                            0, round((perf_counter() - started_at) * 1000)
                        ),
                    )
                self.content_management.save_article_assessment(
                    article.id, assessment, self.llm_model
                )
                if not assessment.rejected and assessment.summary:
                    self.failure_metrics.article_summary_succeeded(
                        max(0, perf_counter() - started_at)
                    )
