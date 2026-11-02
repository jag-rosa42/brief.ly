from src.application.port.topic_catalog import TopicCatalog
from src.domain.entities.topic import Topic


class ListTopics:
    def __init__(self, topic_catalog: TopicCatalog) -> None:
        self._topic_catalog: TopicCatalog = topic_catalog

    def execute(self) -> list[Topic]:
        topics = self._topic_catalog.get_all()
        return sorted(topics.values(), key=lambda topic: topic.id)
