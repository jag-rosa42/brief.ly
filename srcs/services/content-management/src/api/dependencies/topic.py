from typing import Annotated

from fastapi import Depends

from src.api.dependencies.database import UnitOfWorkDep
from src.api.dependencies.repositories import TopicRepositoryDep
from src.application.use_cases.topics import ListTopics, UpdateTopicSummary


def get_list_topics(repository: TopicRepositoryDep) -> ListTopics:
    return ListTopics(repository)


ListTopicsDep = Annotated[
    ListTopics,
    Depends(get_list_topics),
]


def get_update_topic_summary(
    uow: UnitOfWorkDep, repository: TopicRepositoryDep
) -> UpdateTopicSummary:
    return UpdateTopicSummary(uow, repository)


UpdateTopicSummaryDep = Annotated[
    UpdateTopicSummary,
    Depends(get_update_topic_summary),
]
