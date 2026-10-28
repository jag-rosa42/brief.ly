from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

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
