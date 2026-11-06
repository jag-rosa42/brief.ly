from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TopicArticleSummary:
    article_id: UUID
    summary: str | None
