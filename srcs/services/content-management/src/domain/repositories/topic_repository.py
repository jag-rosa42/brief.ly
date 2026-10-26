from typing import Protocol

from src.domain.entities import Topic


class TopicRepository(Protocol):
    def list_all(self) -> list[Topic]: ...
