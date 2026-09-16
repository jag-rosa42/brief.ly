from datetime import datetime

from newsapi import NewsApiClient

from src.domain.entities import DiscoveredArticle, Source


class NewsApiArticleDiscoverer:
    """
    The article discoverer look for top articles for specified
    category and language
    """

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
    def _to_discovered_article(item: dict, source: Source) -> DiscoveredArticle:
        """
        Url is used to identify an already registered article in db.
        """
        published_at = item.get("publishedAt")
        author = item.get("author")
        source_name = item.get("source", {}).get("name")

        return DiscoveredArticle(
            external_id=item["url"],
            url=item["url"],
            publisher_name=source_name,
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
