from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.entities.article_summary import ArticleSummary


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
