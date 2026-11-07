from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from shared_auth import DownstreamClient

from src.application.port.article_catalog import ArticleCatalog
from src.application.port.profile_reader import ProfileReader
from src.application.port.topic_catalog import TopicCatalog
from src.application.use_cases.get_briefing import GetBriefing
from src.infrastructure.clients.article_catalog.http_article_catalog import (
    HttpArticleCatalog,
)
from src.infrastructure.clients.profile_reader.http_profile_reader import (
    HttpProfileReader,
)
from src.infrastructure.clients.topic_catalog.http_topic_catalog import HttpTopicCatalog
from src.infrastructure.config.app import app_settings

# Each client keeps one HTTP connection pool: lru_cache builds it on first use,
# then every request gets the same object.


@lru_cache
def get_profile_reader() -> ProfileReader:
    # The profile belongs to the user: DownstreamClient forwards their token.
    return HttpProfileReader(
        DownstreamClient("personalization", app_settings.PERSONALIZATION_URL)
    )


ProfileReaderDep = Annotated[ProfileReader, Depends(get_profile_reader)]


@lru_cache
def get_topic_catalog() -> TopicCatalog:
    return HttpTopicCatalog(app_settings.CONTENT_MANAGEMENT_URL)


TopicCatalogDep = Annotated[TopicCatalog, Depends(get_topic_catalog)]


@lru_cache
def get_article_catalog() -> ArticleCatalog:
    return HttpArticleCatalog(app_settings.CONTENT_MANAGEMENT_URL)


ArticleCatalogDep = Annotated[ArticleCatalog, Depends(get_article_catalog)]


def get_get_briefing(
    profile_reader: ProfileReaderDep,
    topic_catalog: TopicCatalogDep,
    article_catalog: ArticleCatalogDep,
) -> GetBriefing:
    return GetBriefing(profile_reader, topic_catalog, article_catalog)


GetBriefingDep = Annotated[GetBriefing, Depends(get_get_briefing)]
