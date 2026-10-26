from typing import Annotated

from fastapi import Depends

from src.api.dependencies.database import SessionDep
from src.application.use_cases.topics import ListTopics
from src.domain.repositories import TopicRepository
from src.infrastructure.database.repositories import SqlAlchemyTopicRepository


def get_topic_repository(session: SessionDep) -> TopicRepository:
    return SqlAlchemyTopicRepository(session)


TopicRepositoryDep = Annotated[
    TopicRepository,
    Depends(get_topic_repository),
]


def get_list_topics(repository: TopicRepositoryDep) -> ListTopics:
    return ListTopics(repository)


ListTopicsDep = Annotated[
    ListTopics,
    Depends(get_list_topics),
]
