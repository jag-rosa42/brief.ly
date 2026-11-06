from uuid import UUID

from src.application.exceptions import (
    ArticleCatalogUnavailableError,
    TopicCatalogUnavailableError,
)
from src.domain.entities.article import Article
from src.domain.entities.profile import Profile
from src.domain.entities.topic import Topic


class FakeProfileReader:
    def __init__(self, profile: Profile | None) -> None:
        self._profile = profile
        self.tokens: list[str] = []

    def get(self, user_token: str) -> Profile | None:
        self.tokens.append(user_token)
        return self._profile


class FakeTopicCatalog:
    def __init__(self, topics: list[Topic], available: bool = True) -> None:
        self._topics = {topic.id: topic for topic in topics}
        self._available = available
        self.calls = 0

    def get_all(self) -> dict[str, Topic]:
        self.calls += 1
        if not self._available:
            raise TopicCatalogUnavailableError()
        return dict(self._topics)


class FakeArticleCatalog:
    def __init__(self, articles: list[Article], available: bool = True) -> None:
        self._articles = articles
        self._available = available
        self.calls: list[str] = []

    def list_by_topic(self, topic_id: str) -> list[Article]:
        self.calls.append(topic_id)
        if not self._available:
            raise ArticleCatalogUnavailableError()
        return [article for article in self._articles if article.topic_id == topic_id]


def article(topic_id: str, article_id: UUID) -> Article:
    return Article(
        article_id=article_id,
        title=f"Article about {topic_id}",
        source="TechDaily",
        url="https://example.com/article",
        summary=None,
        read_time_minutes=0,
        topic_id=topic_id,
    )
