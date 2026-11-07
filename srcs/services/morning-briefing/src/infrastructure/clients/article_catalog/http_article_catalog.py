from uuid import UUID

import httpx2 as httpx

from src.application.exceptions import ArticleCatalogUnavailableError
from src.domain.entities.article import Article

# Contract: docs/api/04_content-management.md, GET /internal/v1/articles?topic_id=
# returns {"items": [<article>]}, or 404 TOPIC_NOT_FOUND for an unknown topic.
# We keep the fields of the briefing only.
ARTICLES_PATH = "/internal/v1/articles"
TIMEOUT_SECONDS = 2.0


class HttpArticleCatalog:
    def __init__(self, base_url: str, client: httpx.Client | None = None) -> None:
        # `client` is a parameter so tests can pass a fake one.
        self._client = client or httpx.Client(base_url=base_url, timeout=TIMEOUT_SECONDS)

    def list_by_topic(self, topic_id: str) -> list[Article]:
        try:
            # TODO(service-token): CM will require a service token on /internal/*.
            # When shared_auth's service-token provider exists, add the header here:
            #   headers={"Authorization": f"Bearer {token_provider.get_token()}"}
            # The provider caches the token and renews it before it expires.
            response = self._client.get(ARTICLES_PATH, params={"topic_id": topic_id})
            if response.status_code == httpx.codes.NOT_FOUND:
                return []
            response.raise_for_status()
            articles = [
                Article(
                    article_id=UUID(item["article_id"]),
                    title=item["title"],
                    publisher_name=item["publisher_name"],
                    url=item["url"],
                    summary=item["summary"],
                    read_time_minutes=item["read_time_minutes"],
                    topic_id=item["topic_id"],
                )
                for item in response.json()["items"]
            ]
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
            raise ArticleCatalogUnavailableError() from error

        return articles
