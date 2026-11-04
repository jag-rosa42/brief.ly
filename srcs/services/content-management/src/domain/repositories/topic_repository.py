from typing import Protocol

from src.domain.entities import Topic


class TopicRepository(Protocol):
    def exists(self, topic_id: str) -> bool: ...

    def list_all(self) -> list[Topic]: ...
