from uuid import UUID

from src.application.port.unit_of_work import UnitOfWork
from src.domain.repositories.saved_article_repository import SavedArticleRepository


class DeleteSavedArticle:
    def __init__(
        self, uow: UnitOfWork, saved_article_repository: SavedArticleRepository
    ) -> None:
        self._uow: UnitOfWork = uow
        self._saved_articles: SavedArticleRepository = saved_article_repository

    def execute(self, account_id: UUID, article_id: UUID) -> None:
        with self._uow:
            self._saved_articles.delete(account_id, article_id)
            self._uow.commit()
