from typing import Protocol
from uuid import UUID

from src.domain.entities.saved_article import SavedArticle


class SavedArticleRepository(Protocol):
    def list_for_account(self, account_id: UUID) -> list[SavedArticle]:
        """Return the account's saved articles, most recently saved first."""
        ...

    def add(self, saved_article: SavedArticle) -> SavedArticle:
        """Insert the saved article and return it with its saved_at."""
        ...

    def exists(self, account_id: UUID, article_id: UUID) -> bool:
        """Tell whether the account has already saved this article."""
        ...

    def count_for_account(self, account_id: UUID) -> int:
        """Return how many articles the account has saved."""
        ...

    def delete(self, account_id: UUID, article_id: UUID) -> None:
        """Remove the article from the account's saved articles.

        Does nothing if the article was not saved: deleting is idempotent.
        """
        ...
