from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.api.dependencies.service_token import get_content_management_token_provider
from src.application.port.topic_catalog import TopicCatalog
from src.application.use_cases.list_topics import ListTopics
from src.infrastructure.clients.topic_catalog.http_topic_catalog import HttpTopicCatalog
from src.infrastructure.config.app import app_settings


@lru_cache  # built once, on first use, then always the same object
def get_topic_catalog() -> TopicCatalog:
    return HttpTopicCatalog(
        app_settings.CONTENT_MANAGEMENT_URL,
        get_content_management_token_provider(),
    )


TopicCatalogDep = Annotated[TopicCatalog, Depends(get_topic_catalog)]


def get_list_topics(topic_catalog: TopicCatalogDep) -> ListTopics:
    return ListTopics(topic_catalog)


ListTopicsDep = Annotated[ListTopics, Depends(get_list_topics)]
