from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.entities import NormalizedArticle
from src.infrastructure.database.models import NormalizedArticleModel


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
            .limit(limit)
        )
        return [self._to_domain(model) for model in self._session.scalars(statement)]

    def list_missing_summary(self, limit: int) -> list[NormalizedArticle]:
        statement = (
            select(NormalizedArticleModel)
            .where(NormalizedArticleModel.summary.is_(None))
            .limit(limit)
        )
        return [self._to_domain(model) for model in self._session.scalars(statement)]

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
            summary=normalized_article.summary,
            summarized_at=normalized_article.summarized_at,
            summary_llm_model=normalized_article.summary_llm_model,
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
            summary=model.summary,
            summarized_at=model.summarized_at,
            summary_llm_model=model.summary_llm_model,
        )
