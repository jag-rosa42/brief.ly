from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from src.domain.entities.extracted_article import ExtractedArticle
from src.infrastructure.database.models.article import ArticleModel

# NOTE: The commit is handled in source_repository, when the update
# is done.


class SqlAlchemyArticleRepository:
    def __init__(self, session: Session):
        self._session: Session = session

    def exists(
        self,
        source_id: UUID,
        external_id: str,
    ) -> bool:
        statement = select(
            exists().where(
                ArticleModel.source_id == source_id,
                ArticleModel.external_id == external_id,
            )
        )
        return bool(self._session.scalar(statement))

        # statement = select(ArticleModel).where(
        #             ArticleModel.source_id == source_id,
        #             ArticleModel.external_id == external_id,
        #         )
        # return self._session.scalar(statement) is not None

    def save(
        self,
        source_id: UUID,
        article: ExtractedArticle,
    ) -> None:
        article_model: ArticleModel = self._to_model(article, source_id)
        self._session.add(article_model)
        self._session.flush()

    @staticmethod
    def _to_model(article: ExtractedArticle, source_id: UUID) -> ArticleModel:
        return ArticleModel(
            id=article.id,
            source_id=source_id,
            external_id=article.external_id,
            url=article.url,
            title=article.title,
            editor=article.editor,
            description=article.description,
            content=article.content,
            authors=article.authors,
            image_url=article.image_url,
            published_at=article.published_at,
            category=article.category,
            language=article.language,
        )
