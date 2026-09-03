from datetime import datetime

from newsapi import NewsApiClient

from src.domain.entities.discovered_article import DiscoveredArticle
from src.domain.entities.source import Source


# The discoverer look for top articles for specified category + language
class NewsApiDiscoverer:
    def __init__(self, client: NewsApiClient):
        self.client = client

    def discover(self, source: Source) -> list[DiscoveredArticle]:
        response = self.client.get_top_headlines(
            category=source.category,
            language=source.language,
        )

        return [
            self._to_discovered_article(item, source)
            for item in response["articles"]
            if item.get("url")
        ]

    @staticmethod
    def _to_discovered_article(
            item: dict,
            source: Source
            ) -> DiscoveredArticle:
        published_at = item.get("publishedAt")
        author = item.get("author")

        return DiscoveredArticle(
            external_id=item["url"],
            url=item["url"],
            editor=item["source"]["name"],
            description=item.get("description"),
            category=source.category,
            language=source.language,
            authors=[author] if author else None,
            published_at=(
                datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                if published_at
                else None
            ),
        )
