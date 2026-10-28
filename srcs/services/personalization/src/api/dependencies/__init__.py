from src.api.dependencies.account import (
    ACCOUNT_ID_HEADER_NAME,
    CurrentAccountIdDep,
)
from src.api.dependencies.database import SessionDep, UnitOfWorkDep, get_db
from src.api.dependencies.profile import (
    GetCurrentProfileDep,
    ProfileRepositoryDep,
    UpsertCurrentProfileDep,
)
from src.api.dependencies.saved_article import (
    DeleteSavedArticleDep,
    ListSavedArticlesDep,
    SavedArticleRepositoryDep,
)
from src.api.dependencies.topic_catalog import TopicCatalogDep

__all__: list[str] = [
    "ACCOUNT_ID_HEADER_NAME",
    "CurrentAccountIdDep",
    "DeleteSavedArticleDep",
    "GetCurrentProfileDep",
    "ListSavedArticlesDep",
    "ProfileRepositoryDep",
    "SavedArticleRepositoryDep",
    "SessionDep",
    "TopicCatalogDep",
    "UnitOfWorkDep",
    "UpsertCurrentProfileDep",
    "get_db",
]
