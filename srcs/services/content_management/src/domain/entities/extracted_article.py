from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ExtractedArticle:
    id: UUID
    external_id: str
    url: str
    editor: str
    title: str
    description: str | None
    content: str
    authors: list[str] | None
    image_url: str | None
    category: str
    language: str
    published_at: datetime | None
