from typing import Protocol

from src.domain.entities.article import Article


class ArticleCatalog(Protocol):
    def list_by_topic(self, topic_id: str) -> list[Article]:
        """Return the topic's articles, as Content Management knows them.

        Returns an empty list if Content Management doesn't know the topic.

        Raises:
            ArticleCatalogUnavailableError: if Content Management can't be reached
            or answers with an unexpected response.
        """
        ...
