from dataclasses import dataclass
from datetime import datetime

"""
DiscoveredArticle contains data provided by NewsAPI; The most important value
is the url that the article_extractor will use to fetch the article.
"""


@dataclass(frozen=True)
class DiscoveredArticle:
    external_id: str
    url: str
    publisher_name: str
    description: str | None
    authors: list[str] | None
    published_at: datetime | None
    category: str
    language: str
