from typing import Protocol


class TopicCatalog(Protocol):
    def get_summaries(self) -> dict[str, str | None]:
        """Return every topic's latest summary, indexed by topic id.

        A topic not summarized yet maps to None.

        Raises:
            TopicCatalogUnavailableError: if the catalog cannot be retrieved.
        """
        ...
