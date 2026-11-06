from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Article:
    article_id: UUID
    title: str
    source: str
    topic_id: str
    summary: str | None
    url: str
    read_time_minutes: int
