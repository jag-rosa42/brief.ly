from typing import Annotated

from fastapi import Depends
from newsapi import NewsApiClient

from src.api.dependencies.database import SessionDep, UnitOfWorkDep
from src.application.port import ArticleDiscoverer, ArticleExtractor, IngestionLock
from src.application.use_cases.ingestion import SynchronizeSources
from src.domain.repositories import NormalizedArticleRepository, SourceRepository
from src.infrastructure.clients.article_discovery.newsapi_article_discoverer import (
    NewsApiArticleDiscoverer,
)
from src.infrastructure.clients.article_extraction.newspaper_article_extractor import (
    NewspaperArticleExtractor,
)
from src.infrastructure.config.news_api import NewsApiSettings
from src.infrastructure.database.ingestion_lock import PostgresIngestionLock
from src.infrastructure.database.repositories import (
    SqlAlchemyNormalizedArticleRepository,
    SqlAlchemySourceRepository,
)


def get_source_repository(session: SessionDep) -> SourceRepository:
    return SqlAlchemySourceRepository(session)


SourceRepositoryDep = Annotated[
    SourceRepository,
    Depends(get_source_repository),
]


def get_normalized_article_repository(
    session: SessionDep,
) -> NormalizedArticleRepository:
    return SqlAlchemyNormalizedArticleRepository(session)


NormalizedArticleRepositoryDep = Annotated[
    NormalizedArticleRepository,
    Depends(get_normalized_article_repository),
]


def get_ingestion_lock(session: SessionDep) -> IngestionLock:
    return PostgresIngestionLock(session)


IngestionLockDep = Annotated[IngestionLock, Depends(get_ingestion_lock)]


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


def get_article_extractor() -> ArticleExtractor:
    return NewspaperArticleExtractor()


ArticleExtractorDep = Annotated[
    ArticleExtractor,
    Depends(get_article_extractor),
]


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
