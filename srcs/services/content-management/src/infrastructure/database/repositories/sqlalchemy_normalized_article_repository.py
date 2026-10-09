from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from src.domain.entities import NormalizedArticle
from src.infrastructure.database.models import NormalizedArticleModel

# NOTE: The commit is handled in source_repository, when the update
# is done.


class SqlAlchemyNormalizedArticleRepository:
    def __init__(self, session: Session):
        self._session: Session = session

    def exists(
        self,
        source_id: UUID,
        external_id: str,
    ) -> bool:
        statement = select(
            exists().where(
                NormalizedArticleModel.source_id == source_id,
                NormalizedArticleModel.discovered_article_external_id == external_id,
            )
        )
        return bool(self._session.scalar(statement))

    def save(
        self,
        source_id: UUID,
        normalized_article: NormalizedArticle,
    ) -> None:
        normalized_article_model: NormalizedArticleModel = self._to_model(
            normalized_article, source_id
        )
        self._session.add(normalized_article_model)
        self._session.flush()

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
        )
