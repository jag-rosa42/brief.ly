from uuid import UUID

from src.application.port.article_catalog import ArticleCatalog
from src.application.port.unit_of_work import UnitOfWork
from src.domain.entities.article import Article
from src.domain.entities.saved_article import MAX_SAVED_ARTICLES, SavedArticle
from src.domain.exception import (
    ArticleAlreadySavedError,
    ArticleNotFoundError,
    ProfileNotFoundError,
    SavedArticlesLimitReachedError,
)
from src.domain.repositories.profile_repository import ProfileRepository
from src.domain.repositories.saved_article_repository import SavedArticleRepository


class SaveArticle:
    def __init__(
        self,
        uow: UnitOfWork,
        profile_repository: ProfileRepository,
        saved_article_repository: SavedArticleRepository,
        article_catalog: ArticleCatalog,
    ) -> None:
        self._uow: UnitOfWork = uow
        self._profiles: ProfileRepository = profile_repository
        self._saved_articles: SavedArticleRepository = saved_article_repository
        self._article_catalog: ArticleCatalog = article_catalog

    def execute(self, account_id: UUID, article_id: UUID) -> SavedArticle:
        # Called before the transaction: no row lock is held while waiting
        # for Content Management.
        article: Article | None = self._article_catalog.find_by_id(article_id)
        if article is None:
            raise ArticleNotFoundError()

        with self._uow:
            # Locking the profile serializes the saves of one account, so two
            # concurrent saves can't both pass the limit check.
            if self._profiles.find_by_id_for_update(account_id) is None:
                raise ProfileNotFoundError()
            if self._saved_articles.exists(account_id, article_id):
                raise ArticleAlreadySavedError()
            if self._saved_articles.count_for_account(account_id) >= MAX_SAVED_ARTICLES:
                raise SavedArticlesLimitReachedError(MAX_SAVED_ARTICLES)

            saved: SavedArticle = self._saved_articles.add(
                SavedArticle.create(account_id, article)
            )
            self._uow.commit()

        return saved
