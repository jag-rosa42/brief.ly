from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Article:
    article_id: UUID
    title: str
    source: str
    url: str
    summary: str | None
    read_time_minutes: int
    topic_id: str
