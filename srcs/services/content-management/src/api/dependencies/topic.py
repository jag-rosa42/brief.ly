from typing import Annotated

from fastapi import Depends

from src.api.dependencies.repositories import TopicRepositoryDep
from src.application.use_cases.topics import ListTopics


def get_list_topics(repository: TopicRepositoryDep) -> ListTopics:
    return ListTopics(repository)


ListTopicsDep = Annotated[
    ListTopics,
    Depends(get_list_topics),
]
