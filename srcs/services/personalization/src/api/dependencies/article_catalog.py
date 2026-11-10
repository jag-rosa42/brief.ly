from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.api.dependencies.clients import get_content_management_client
from src.api.dependencies.database import UnitOfWorkDep
from src.api.dependencies.profile import ProfileRepositoryDep
from src.api.dependencies.saved_article import SavedArticleRepositoryDep
from src.api.dependencies.service_token import get_content_management_token_provider
from src.application.port.article_catalog import ArticleCatalog
from src.application.use_cases.save_article import SaveArticle
from src.infrastructure.clients.article_catalog.http_article_catalog import (
    HttpArticleCatalog,
)


@lru_cache  # built once, on first use, then always the same object
def get_article_catalog() -> ArticleCatalog:
    return HttpArticleCatalog(
        get_content_management_client(),
        get_content_management_token_provider(),
    )


ArticleCatalogDep = Annotated[ArticleCatalog, Depends(get_article_catalog)]


# Here and not in saved_article.py: profile.py already imports saved_article.py,
# so importing profile.py from there would be circular.
def get_save_article(
    uow: UnitOfWorkDep,
    profile_repository: ProfileRepositoryDep,
    saved_article_repository: SavedArticleRepositoryDep,
    article_catalog: ArticleCatalogDep,
) -> SaveArticle:
    return SaveArticle(uow, profile_repository, saved_article_repository, article_catalog)


SaveArticleDep = Annotated[SaveArticle, Depends(get_save_article)]
