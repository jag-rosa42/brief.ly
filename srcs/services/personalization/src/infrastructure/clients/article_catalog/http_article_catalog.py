from http import HTTPStatus
from uuid import UUID

from shared_auth import DownstreamClient, DownstreamError, TokenExpiredError
from shared_errors import InfrastructureError

from src.application.exceptions import ArticleCatalogUnavailableError
from src.domain.entities.article import Article
from src.infrastructure.clients.content_management import CONTENT_MANAGEMENT_SERVICE
from src.infrastructure.clients.service_token_provider import ServiceTokenProvider

# Contract of Content Management's PR #179: GET /internal/v1/articles/{article_id}
# returns the article object of docs/api/04_content-management.md, or 404
# ARTICLE_NOT_FOUND when the article is unknown or its summary was rejected.
# We keep the fields of the snapshot only, and store `publisher_name` as `source`.
ARTICLES_PATH = "/internal/v1/articles/{article_id}"

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

    def find_by_id(self, article_id: UUID) -> Article | None:
        try:
            data = self._client.get_json(
                ARTICLES_PATH.format(article_id=article_id),
                token=self._token_provider.get_token(),
            )
        except DownstreamError as error:
            # Only Content Management's 404 means "unknown article": a 404
            # from Identity (wrong IDENTITY_URL) is a failure like any other.
            if (
                error.service == CONTENT_MANAGEMENT_SERVICE
                and error.status_code == HTTPStatus.NOT_FOUND
            ):
                return None
            raise ArticleCatalogUnavailableError() from error
        except (
            InfrastructureError,
            TokenExpiredError,
            ValueError,  # the body is not JSON
        ) as error:
            raise ArticleCatalogUnavailableError() from error

        try:
            return Article(
                article_id=UUID(data["article_id"]),
                title=data["title"],
                source=data["publisher_name"],
                topic_id=data["topic_id"],
                summary=data["summary"],
                url=data["url"],
                read_time_minutes=data["read_time_minutes"],
            )
        except (ValueError, KeyError, TypeError) as error:
            raise ArticleCatalogUnavailableError() from error
