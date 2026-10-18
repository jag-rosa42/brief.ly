from src.application.ports import TopicRepository
from src.domain.entities import Topic


class ListTopics:
    def __init__(self, repository: TopicRepository):
        self._repository = repository

    def execute(self) -> list[Topic]:
        return self._repository.list_all()
