from http import HTTPStatus
from uuid import UUID

from shared_auth import DownstreamClient, DownstreamError, TokenExpiredError
from shared_errors import InfrastructureError

from src.application.exceptions import ArticleCatalogUnavailableError
from src.domain.entities.article import Article
from src.infrastructure.clients.content_management import CONTENT_MANAGEMENT_SERVICE
from src.infrastructure.clients.service_token_provider import ServiceTokenProvider

# Contract: docs/api/04_content-management.md, GET /internal/v1/articles?topic_id=
# returns {"items": [<article>]}, or 404 TOPIC_NOT_FOUND for an unknown topic.
# We keep the fields of the briefing only.
ARTICLES_PATH = "/internal/v1/articles"

# DownstreamClient turns every failure into one of our errors: Content
# Management unreachable or 502/503/504 -> InfrastructureError, 401
# TOKEN_EXPIRED -> TokenExpiredError, any other error answer ->
# DownstreamError. The token provider raises InfrastructureError (Identity
# unreachable) or DownstreamError (Identity refused our credentials).
# TokenExpiredError is caught on purpose: it's our service token that
# expired, not the user's, so it must not reach the frontend as the user's
# TOKEN_EXPIRED.


class HttpArticleCatalog:
    def __init__(
        self, client: DownstreamClient, token_provider: ServiceTokenProvider
    ) -> None:
        self._client = client
        self._token_provider = token_provider

    def list_by_topic(self, topic_id: str) -> list[Article]:
        try:
            data = self._client.get_json(
                ARTICLES_PATH,
                token=self._token_provider.get_token(),
                params={"topic_id": topic_id},
            )
        except DownstreamError as error:
            # Only Content Management's 404 means "unknown topic": a 404 from
            # Identity (wrong IDENTITY_URL) is a failure like any other.
            if (
                error.service == CONTENT_MANAGEMENT_SERVICE
                and error.status_code == HTTPStatus.NOT_FOUND
            ):
                return []
            raise ArticleCatalogUnavailableError() from error
        except (
            InfrastructureError,
            TokenExpiredError,
            ValueError,  # the body is not JSON
        ) as error:
            raise ArticleCatalogUnavailableError() from error

        try:
            return [
                Article(
                    article_id=UUID(item["article_id"]),
                    title=item["title"],
                    publisher_name=item["publisher_name"],
                    url=item["url"],
                    summary=item["summary"],
                    read_time_minutes=item["read_time_minutes"],
                    topic_id=item["topic_id"],
                )
                for item in data["items"]
            ]
        except (ValueError, KeyError, TypeError) as error:
            raise ArticleCatalogUnavailableError() from error
