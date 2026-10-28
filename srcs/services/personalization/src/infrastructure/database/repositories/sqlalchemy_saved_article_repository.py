from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.domain.entities.saved_article import SavedArticle
from src.infrastructure.database.models.saved_article import (
    SavedArticle as SavedArticleModel,
)


class SqlAlchemySavedArticleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_account(self, account_id: UUID) -> list[SavedArticle]:
        models = self._session.execute(
            select(SavedArticleModel)
            .where(SavedArticleModel.account_id == account_id)
            .order_by(SavedArticleModel.saved_at.desc())
        ).scalars()
        return [self._to_domain(model) for model in models]

    def delete(self, account_id: UUID, article_id: UUID) -> None:
        self._session.execute(
            delete(SavedArticleModel).where(
                SavedArticleModel.account_id == account_id,
                SavedArticleModel.article_id == article_id,
            )
        )

    @staticmethod
    def _to_domain(model: SavedArticleModel) -> SavedArticle:
        return SavedArticle(
            account_id=model.account_id,
            article_id=model.article_id,
            title=model.title,
            source=model.source,
            topic_id=model.topic_id,
            summary=model.summary,
            url=model.url,
            read_time_minutes=model.read_time_minutes,
            saved_at=model.saved_at,
        )
