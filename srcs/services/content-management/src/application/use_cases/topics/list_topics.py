from src.domain.entities import Topic
from src.domain.repositories import TopicRepository


class ListTopics:
    def __init__(self, repository: TopicRepository) -> None:
        self._repository = repository

    def execute(self) -> list[Topic]:
        return self._repository.list_all()
