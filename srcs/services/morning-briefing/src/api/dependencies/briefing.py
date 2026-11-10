from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.api.dependencies.clients import (
    get_content_management_client,
    get_personalization_client,
)
from src.api.dependencies.service_token import get_content_management_token_provider
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

# Built once, on first use (lru_cache), then every request gets the same object.


@lru_cache
def get_profile_reader() -> ProfileReader:
    return HttpProfileReader(get_personalization_client())


ProfileReaderDep = Annotated[ProfileReader, Depends(get_profile_reader)]


@lru_cache
def get_topic_catalog() -> TopicCatalog:
    return HttpTopicCatalog(
        get_content_management_client(),
        get_content_management_token_provider(),
    )


TopicCatalogDep = Annotated[TopicCatalog, Depends(get_topic_catalog)]


@lru_cache
def get_article_catalog() -> ArticleCatalog:
    return HttpArticleCatalog(
        get_content_management_client(),
        get_content_management_token_provider(),
    )


ArticleCatalogDep = Annotated[ArticleCatalog, Depends(get_article_catalog)]


def get_get_briefing(
    profile_reader: ProfileReaderDep,
    topic_catalog: TopicCatalogDep,
    article_catalog: ArticleCatalogDep,
) -> GetBriefing:
    return GetBriefing(profile_reader, topic_catalog, article_catalog)


GetBriefingDep = Annotated[GetBriefing, Depends(get_get_briefing)]
