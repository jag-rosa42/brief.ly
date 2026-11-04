from typing import Annotated

from fastapi import Depends
from newsapi import NewsApiClient

from src.api.dependencies.database import UnitOfWorkDep
from src.api.dependencies.repositories import (
    NormalizedArticleRepositoryDep,
    SourceRepositoryDep,
)
from src.application.port import ArticleDiscoverer, ArticleExtractor, IngestionLock
from src.application.use_cases.ingestion import SynchronizeSources
from src.infrastructure.clients.article_discovery.newsapi_article_discoverer import (
    NewsApiArticleDiscoverer,
)
from src.infrastructure.clients.article_extraction.newspaper_article_extractor import (
    NewspaperArticleExtractor,
)
from src.infrastructure.config.news_api import NewsApiSettings
from src.infrastructure.database.config import engine
from src.infrastructure.database.ingestion_lock import PostgresIngestionLock


# ---------------------------------------------------------------------------
# Ingestion Lock
# ---------------------------------------------------------------------------
def get_ingestion_lock() -> IngestionLock:
    return PostgresIngestionLock(engine)


IngestionLockDep = Annotated[IngestionLock, Depends(get_ingestion_lock)]


# ---------------------------------------------------------------------------
# Article Discoverer
# ---------------------------------------------------------------------------
def get_article_discoverer() -> ArticleDiscoverer:
    newsapi_settings = NewsApiSettings()
    client = NewsApiClient(
        api_key=newsapi_settings.NEWS_API_KEY.get_secret_value(),
    )
    return NewsApiArticleDiscoverer(client)


ArticleDiscovererDep = Annotated[
    ArticleDiscoverer,
    Depends(get_article_discoverer),
]


# ---------------------------------------------------------------------------
# Article Extractor
# ---------------------------------------------------------------------------
def get_article_extractor() -> ArticleExtractor:
    return NewspaperArticleExtractor()


ArticleExtractorDep = Annotated[
    ArticleExtractor,
    Depends(get_article_extractor),
]


# ---------------------------------------------------------------------------
# Synchronize Sources
# ---------------------------------------------------------------------------
def get_synchronize_sources(
    uow: UnitOfWorkDep,
    ingestion_lock: IngestionLockDep,
    source_repository: SourceRepositoryDep,
    normalized_article_repository: NormalizedArticleRepositoryDep,
    article_discoverer: ArticleDiscovererDep,
    article_extractor: ArticleExtractorDep,
) -> SynchronizeSources:
    return SynchronizeSources(
        uow=uow,
        ingestion_lock=ingestion_lock,
        source_repository=source_repository,
        normalized_article_repository=normalized_article_repository,
        article_discoverer=article_discoverer,
        article_extractor=article_extractor,
    )


SynchronizeSourcesDep = Annotated[
    SynchronizeSources,
    Depends(get_synchronize_sources),
]
