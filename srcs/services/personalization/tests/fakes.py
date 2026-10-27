from src.application.exceptions import TopicCatalogUnavailableError
from src.domain.entities.topic import Topic


class FakeTopicCatalog:
    def __init__(self, topic_ids: list[str], available: bool = True) -> None:
        self._topic_ids = topic_ids
        self._available = available
        self.calls = 0

    def get_all(self) -> dict[str, Topic]:
        self.calls += 1
        if not self._available:
            raise TopicCatalogUnavailableError()
        return {topic_id: Topic(id=topic_id) for topic_id in self._topic_ids}
