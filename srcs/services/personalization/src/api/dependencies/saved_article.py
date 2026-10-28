from typing import Annotated

from fastapi import Depends

from src.api.dependencies.database import SessionDep, UnitOfWorkDep
from src.application.use_cases.delete_saved_article import DeleteSavedArticle
from src.application.use_cases.list_saved_articles import ListSavedArticles
from src.domain.repositories.saved_article_repository import SavedArticleRepository
from src.infrastructure.database.repositories.sqlalchemy_saved_article_repository import (
    SqlAlchemySavedArticleRepository,
)


def get_saved_article_repository(session: SessionDep) -> SavedArticleRepository:
    return SqlAlchemySavedArticleRepository(session)


SavedArticleRepositoryDep = Annotated[
    SavedArticleRepository, Depends(get_saved_article_repository)
]


def get_list_saved_articles(
    saved_article_repository: SavedArticleRepositoryDep,
) -> ListSavedArticles:
    return ListSavedArticles(saved_article_repository)


ListSavedArticlesDep = Annotated[ListSavedArticles, Depends(get_list_saved_articles)]


def get_delete_saved_article(
    uow: UnitOfWorkDep,
    saved_article_repository: SavedArticleRepositoryDep,
) -> DeleteSavedArticle:
    return DeleteSavedArticle(uow, saved_article_repository)


DeleteSavedArticleDep = Annotated[DeleteSavedArticle, Depends(get_delete_saved_article)]
