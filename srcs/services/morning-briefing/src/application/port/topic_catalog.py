from typing import Protocol

from src.domain.entities.topic import Topic


class TopicCatalog(Protocol):
    def get_all(self) -> dict[str, Topic]:
        """Return every topic known to Content Management, indexed by id.

        Raises:
            TopicCatalogUnavailableError: if the catalog cannot be retrieved.
        """
        ...
