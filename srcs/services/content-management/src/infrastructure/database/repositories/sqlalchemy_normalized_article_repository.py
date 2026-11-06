from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.entities import ArticleSummary, NormalizedArticle
from src.infrastructure.database.models import ArticleSummaryModel, NormalizedArticleModel


class SqlAlchemyNormalizedArticleRepository:
    def __init__(self, session: Session) -> None:
        self._session: Session = session

    def list_by_topic_id(
        self,
        topic_id: str,
        limit: int,
    ) -> list[NormalizedArticle]:
        statement = (
            select(NormalizedArticleModel)
            .where(NormalizedArticleModel.category == topic_id)
            .where(
                ~NormalizedArticleModel.summary.has(
                    ArticleSummaryModel.rejected.is_(True)
                )
            )
            .limit(limit)
        )
        return [self._to_domain(model) for model in self._session.scalars(statement)]

    def list_missing_summary(self, limit: int) -> list[NormalizedArticle]:
        statement = (
            select(NormalizedArticleModel)
            .where(~NormalizedArticleModel.summary.has())
            .limit(limit)
        )
        return [self._to_domain(model) for model in self._session.scalars(statement)]

    def get_by_id(self, article_id: UUID) -> NormalizedArticle | None:
        article = self._session.get(NormalizedArticleModel, article_id)
        if article is None:
            return None
        return self._to_domain(article)

    def find_existing_external_ids(
        self,
        source_id: UUID,
        external_ids: list[str],
    ) -> set[str]:
        if not external_ids:
            return set()

        statement = select(NormalizedArticleModel.discovered_article_external_id).where(
            NormalizedArticleModel.source_id == source_id,
            NormalizedArticleModel.discovered_article_external_id.in_(external_ids),
        )
        return set(self._session.scalars(statement))

    def save(
        self,
        source_id: UUID,
        normalized_article: NormalizedArticle,
    ) -> None:
        normalized_article_model: NormalizedArticleModel = self._to_model(
            normalized_article, source_id
        )
        self._session.add(normalized_article_model)

    def update_summary(
        self,
        article_id: UUID,
        summary: ArticleSummary,
    ) -> NormalizedArticle | None:
        article = self._session.get(NormalizedArticleModel, article_id)
        if article is None:
            return None
        if article.summary is None:
            article.summary = self._summary_to_model(summary, article_id)
        else:
            article.summary.text = summary.text
            article.summary.summarized_at = summary.summarized_at
            article.summary.llm_model = summary.llm_model
            article.summary.rejected = summary.rejected
            article.summary.quality_comment = summary.quality_comment
            article.summary.generation_duration_ms = summary.generation_duration_ms
        return self._to_domain(article)

    @staticmethod
    def _to_model(
        normalized_article: NormalizedArticle, source_id: UUID
    ) -> NormalizedArticleModel:
        return NormalizedArticleModel(
            id=normalized_article.id,
            source_id=source_id,
            discovered_article_external_id=(
                normalized_article.discovered_article_external_id
            ),
            url=normalized_article.url,
            title=normalized_article.title,
            publisher_name=normalized_article.publisher_name,
            description=normalized_article.description,
            content=normalized_article.content,
            authors=normalized_article.authors,
            image_url=normalized_article.image_url,
            published_at=normalized_article.published_at,
            category=normalized_article.category,
            language=normalized_article.language,
            summary=(
                SqlAlchemyNormalizedArticleRepository._summary_to_model(
                    normalized_article.summary,
                    normalized_article.id,
                )
                if normalized_article.summary is not None
                else None
            ),
        )

    @staticmethod
    def _to_domain(model: NormalizedArticleModel) -> NormalizedArticle:
        return NormalizedArticle(
            id=model.id,
            discovered_article_external_id=model.discovered_article_external_id,
            url=model.url,
            publisher_name=model.publisher_name,
            title=model.title,
            description=model.description,
            content=model.content,
            authors=model.authors,
            image_url=model.image_url,
            published_at=model.published_at,
            category=model.category,
            language=model.language,
            summary=(
                SqlAlchemyNormalizedArticleRepository._summary_to_domain(model.summary)
                if model.summary is not None
                else None
            ),
        )

    @staticmethod
    def _summary_to_model(
        summary: ArticleSummary,
        article_id: UUID,
    ) -> ArticleSummaryModel:
        return ArticleSummaryModel(
            article_id=article_id,
            text=summary.text,
            summarized_at=summary.summarized_at,
            llm_model=summary.llm_model,
            rejected=summary.rejected,
            quality_comment=summary.quality_comment,
            generation_duration_ms=summary.generation_duration_ms,
        )

    @staticmethod
    def _summary_to_domain(model: ArticleSummaryModel) -> ArticleSummary:
        return ArticleSummary(
            text=model.text,
            summarized_at=model.summarized_at,
            llm_model=model.llm_model,
            rejected=model.rejected,
            quality_comment=model.quality_comment,
            generation_duration_ms=model.generation_duration_ms,
        )
