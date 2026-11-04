from .article import GetArticleDep, ListArticlesDep, UpdateArticleSummaryDep
from .database import SessionDep, UnitOfWorkDep
from .ingestion import (
    ArticleDiscovererDep,
    ArticleExtractorDep,
    IngestionLockDep,
    SynchronizeSourcesDep,
)
from .repositories import (
    NormalizedArticleRepositoryDep,
    SourceRepositoryDep,
    TopicRepositoryDep,
)
from .topic import ListTopicsDep

__all__: list[str] = [
    "ArticleDiscovererDep",
    "ArticleExtractorDep",
    "GetArticleDep",
    "IngestionLockDep",
    "ListArticlesDep",
    "ListTopicsDep",
    "NormalizedArticleRepositoryDep",
    "SessionDep",
    "SourceRepositoryDep",
    "SynchronizeSourcesDep",
    "TopicRepositoryDep",
    "UnitOfWorkDep",
    "UpdateArticleSummaryDep",
]
