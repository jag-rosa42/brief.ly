from uuid import UUID

from src.domain.entities.saved_article import SavedArticle
from src.domain.repositories.saved_article_repository import SavedArticleRepository


class ListSavedArticles:
    def __init__(self, saved_article_repository: SavedArticleRepository) -> None:
        self._saved_articles: SavedArticleRepository = saved_article_repository

    def execute(self, account_id: UUID) -> list[SavedArticle]:
        return self._saved_articles.list_for_account(account_id)
