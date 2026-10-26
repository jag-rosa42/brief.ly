from .database import SessionDep, UnitOfWorkDep, get_db, get_unit_of_work
from .ingestion import (
    ArticleDiscovererDep,
    ArticleExtractorDep,
    IngestionLockDep,
    NormalizedArticleRepositoryDep,
    SourceRepositoryDep,
    SynchronizeSourcesDep,
    get_article_discoverer,
    get_article_extractor,
    get_ingestion_lock,
    get_normalized_article_repository,
    get_source_repository,
    get_synchronize_sources,
)
from .topic import ListTopicsDep, TopicRepositoryDep

__all__: list[str] = [
    "ArticleDiscovererDep",
    "ArticleExtractorDep",
    "IngestionLockDep",
    "ListTopicsDep",
    "NormalizedArticleRepositoryDep",
    "SessionDep",
    "SourceRepositoryDep",
    "SynchronizeSourcesDep",
    "TopicRepositoryDep",
    "UnitOfWorkDep",
    "get_article_discoverer",
    "get_article_extractor",
    "get_db",
    "get_ingestion_lock",
    "get_normalized_article_repository",
    "get_source_repository",
    "get_synchronize_sources",
    "get_unit_of_work",
]
