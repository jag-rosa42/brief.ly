from typing import Protocol
from uuid import UUID

from src.domain.entities.saved_article import SavedArticle


class SavedArticleRepository(Protocol):
    def list_for_account(self, account_id: UUID) -> list[SavedArticle]:
        """Return the account's saved articles, most recently saved first."""
        ...

    def delete(self, account_id: UUID, article_id: UUID) -> None:
        """Remove the article from the account's saved articles.

        Does nothing if the article was not saved: deleting is idempotent.
        """
        ...
