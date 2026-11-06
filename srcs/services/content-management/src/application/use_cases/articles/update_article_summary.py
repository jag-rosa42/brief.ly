from datetime import UTC, datetime
from uuid import UUID

from src.application.port import UnitOfWork
from src.domain.entities import ArticleSummary, NormalizedArticle
from src.domain.exception import ArticleNotFoundError
from src.domain.repositories import ArticleSummaryRepository


class UpdateArticleSummary:
    def __init__(
        self,
        uow: UnitOfWork,
        repository: ArticleSummaryRepository,
    ) -> None:
        self._uow = uow
        self._repository = repository

    def execute(
        self,
        article_id: UUID,
        text: str | None,
        llm_model: str,
        rejected: bool,
        quality_comment: str,
        generation_duration_ms: int,
    ) -> NormalizedArticle:
        with self._uow:
            article = self._repository.get_by_id(article_id)
            if article is None:
                raise ArticleNotFoundError()

            if (
                article.summary is not None
                and article.summary.text == text
                and article.summary.llm_model == llm_model
                and article.summary.rejected == rejected
                and article.summary.quality_comment == quality_comment
                and article.summary.generation_duration_ms == generation_duration_ms
            ):
                return article

            summary = ArticleSummary(
                text=text,
                summarized_at=datetime.now(UTC),
                llm_model=llm_model,
                rejected=rejected,
                quality_comment=quality_comment,
                generation_duration_ms=generation_duration_ms,
            )
            updated_article = self._repository.update_summary(
                article_id=article_id,
                summary=summary,
            )
            if updated_article is None:
                raise ArticleNotFoundError()

            self._uow.flush()
            self._uow.commit()
            return updated_article
