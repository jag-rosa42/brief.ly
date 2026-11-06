from typing import Protocol
from uuid import UUID

from src.domain.entities.article import Article


class ArticleCatalog(Protocol):
    def find_by_id(self, article_id: UUID) -> Article | None:
        """Return the article with this id, as Content Management knows it.

        Returns None if Content Management doesn't know the article
        (404, which also covers a rejected article).

        Raises:
            ArticleCatalogUnavailableError: if Content Management can't be reached
            or answers with an unexpected response.
        """
