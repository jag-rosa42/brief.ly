from uuid import UUID

import httpx2 as httpx

from src.application.exceptions import ArticleCatalogUnavailableError
from src.domain.entities.article import Article

# Contract of Content Management's PR #179: GET /internal/v1/articles/{article_id}
# returns the article object of docs/api/04_content-management.md, or 404
# ARTICLE_NOT_FOUND when the article is unknown or its summary was rejected.
# We keep the fields of the snapshot only, and store `publisher_name` as `source`.
ARTICLES_PATH = "/internal/v1/articles/{article_id}"
TIMEOUT_SECONDS = 2.0


class HttpArticleCatalog:
    def __init__(self, base_url: str, client: httpx.Client | None = None) -> None:
        # `client` is a parameter so tests can pass a fake one.
        self._client = client or httpx.Client(base_url=base_url, timeout=TIMEOUT_SECONDS)

    def find_by_id(self, article_id: UUID) -> Article | None:
        try:
            # TODO(service-token): CM will require a service token on /internal/*.
            # When shared_auth's service-token provider exists, add the header here:
            #   headers={"Authorization": f"Bearer {token_provider.get_token()}"}
            # The provider caches the token and renews it before it expires.
            response = self._client.get(ARTICLES_PATH.format(article_id=article_id))
            if response.status_code == httpx.codes.NOT_FOUND:
                return None
            response.raise_for_status()
            data = response.json()
            article = Article(
                article_id=UUID(data["article_id"]),
                title=data["title"],
                source=data["publisher_name"],
                topic_id=data["topic_id"],
                summary=data["summary"],
                url=data["url"],
                read_time_minutes=data["read_time_minutes"],
            )

        except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
            raise ArticleCatalogUnavailableError() from error

        return article
