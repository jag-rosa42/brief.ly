from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DiscoveredArticle:
    external_id: str
    url: str
    editor: str
    description: str | None
    authors: list[str] | None
    published_at: datetime | None
    category: str
    language: str
