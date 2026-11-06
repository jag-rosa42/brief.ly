from dataclasses import dataclass
from datetime import datetime
from math import ceil
from uuid import UUID

from src.domain.entities.article_summary import ArticleSummary

SUMMARY_WORDS_PER_MINUTE = 200


@dataclass(frozen=True)
class NormalizedArticle:
    id: UUID
    discovered_article_external_id: str
    url: str
    publisher_name: str
    title: str
    description: str | None
    content: str
    authors: list[str] | None
    image_url: str | None
    category: str
    language: str
    published_at: datetime | None
    summary: ArticleSummary | None = None

    @property
    def read_time_minutes(self) -> int:
        if self.summary is None or self.summary.rejected or self.summary.text is None:
            return 0
        summary_words = self.summary.text.split()
        if not summary_words:
            return 0
        return ceil(len(summary_words) / SUMMARY_WORDS_PER_MINUTE)
