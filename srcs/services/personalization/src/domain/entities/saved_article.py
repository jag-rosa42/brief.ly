from dataclasses import dataclass, field
from datetime import datetime
from typing import Self
from uuid import UUID

from src.domain.entities.article import Article

MAX_SAVED_ARTICLES = 12


@dataclass(frozen=True)
class SavedArticle:
    account_id: UUID
    article_id: UUID
    title: str
    source: str
    topic_id: str
    summary: str | None
    url: str
    read_time_minutes: int
    saved_at: datetime | None = field(default=None, compare=False)

    @classmethod
    def create(cls, account_id: UUID, article: Article) -> Self:
        """Snapshot of the article as Content Management returned it."""
        return cls(
            account_id=account_id,
            article_id=article.article_id,
            title=article.title,
            source=article.source,
            topic_id=article.topic_id,
            summary=article.summary,
            url=article.url,
            read_time_minutes=article.read_time_minutes,
        )
