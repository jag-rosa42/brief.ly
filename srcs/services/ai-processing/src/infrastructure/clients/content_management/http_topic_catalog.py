from shared_auth import DownstreamClient, DownstreamError, TokenExpiredError
from shared_errors import InfrastructureError

from src.application.exceptions import TopicCatalogUnavailableError
from src.infrastructure.clients.service_token_provider import ServiceTokenProvider

# Contract: docs/api/04_content-management.md, GET /internal/v1/topics.
# A bare array of topic objects, each with its latest `summary` (or null).
# Same catalog as Morning Briefing's (its http_topic_catalog.py).
#
# Every failure becomes TopicCatalogUnavailableError (503). TokenExpiredError
# is caught on purpose: it's our service token that expired, not the user's,
# so it must not reach the frontend as the user's TOKEN_EXPIRED.
TOPICS_PATH = "/internal/v1/topics"


class HttpTopicCatalog:
    def __init__(
        self, client: DownstreamClient, token_provider: ServiceTokenProvider
    ) -> None:
        self._client = client
        self._token_provider = token_provider

    def get_summaries(self) -> dict[str, str | None]:
        try:
            items = self._client.get_json(
                TOPICS_PATH, token=self._token_provider.get_token()
            )
            summaries = {item["id"]: item.get("summary") for item in items}
        except (
            InfrastructureError,
            DownstreamError,
            TokenExpiredError,
            ValueError,  # the body is not JSON
            KeyError,
            TypeError,
            AttributeError,  # an item is not an object
        ) as error:
            raise TopicCatalogUnavailableError() from error

        if not all(
            isinstance(topic_id, str) and (summary is None or isinstance(summary, str))
            for topic_id, summary in summaries.items()
        ):
            raise TopicCatalogUnavailableError()
        return summaries
