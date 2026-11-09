from uuid import UUID

import httpx2 as httpx
from shared_auth import DownstreamError
from shared_errors import InfrastructureError

from src.application.exceptions import ArticleCatalogUnavailableError
from src.domain.entities.article import Article
from src.infrastructure.clients.token_provider import TokenProvider

# Contract: docs/api/04_content-management.md, GET /internal/v1/articles?topic_id=
# returns {"items": [<article>]}, or 404 TOPIC_NOT_FOUND for an unknown topic.
# We keep the fields of the briefing only.
ARTICLES_PATH = "/internal/v1/articles"
TIMEOUT_SECONDS = 2.0


class HttpArticleCatalog:
    def __init__(
        self,
        base_url: str,
        token_provider: TokenProvider,
        client: httpx.Client | None = None,
    ) -> None:
        self._token_provider = token_provider
        # `client` is a parameter so tests can pass a fake one.
        self._client = client or httpx.Client(base_url=base_url, timeout=TIMEOUT_SECONDS)

    def list_by_topic(self, topic_id: str) -> list[Article]:
        try:
            headers = {"Authorization": f"Bearer {self._token_provider.get_token()}"}
            response = self._client.get(
                ARTICLES_PATH, params={"topic_id": topic_id}, headers=headers
            )
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
        except (
            httpx.HTTPError,
            ValueError,
            KeyError,
            TypeError,
            InfrastructureError,  # Identity unreachable: no token
            DownstreamError,  # Identity refused our credentials
        ) as error:
            raise ArticleCatalogUnavailableError() from error

        return articles
