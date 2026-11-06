from src.api.dependencies.article_catalog import ArticleCatalogDep, SaveArticleDep
from src.api.dependencies.database import SessionDep, UnitOfWorkDep, get_db
from src.api.dependencies.profile import (
    GetCurrentProfileDep,
    GetInternalProfileDep,
    ProfileRepositoryDep,
    UpsertCurrentProfileDep,
)
from src.api.dependencies.saved_article import (
    DeleteSavedArticleDep,
    ListSavedArticlesDep,
    SavedArticleRepositoryDep,
)
from src.api.dependencies.topic_catalog import ListTopicsDep, TopicCatalogDep

__all__: list[str] = [
    "ArticleCatalogDep",
    "DeleteSavedArticleDep",
    "GetCurrentProfileDep",
    "GetInternalProfileDep",
    "ListSavedArticlesDep",
    "ListTopicsDep",
    "ProfileRepositoryDep",
    "SaveArticleDep",
    "SavedArticleRepositoryDep",
    "SessionDep",
    "TopicCatalogDep",
    "UnitOfWorkDep",
    "UpsertCurrentProfileDep",
    "get_db",
]
