from shared_auth import DownstreamClient, DownstreamError, TokenExpiredError
from shared_errors import InfrastructureError

from src.application.exceptions import TopicCatalogUnavailableError
from src.domain.entities.topic import Topic
from src.infrastructure.clients.service_token_provider import ServiceTokenProvider

# Contract of Content Management's PR #140: GET /internal/v1/topics -> [{"id": str}]
TOPICS_PATH = "/internal/v1/topics"

# DownstreamClient turns every failure into one of our errors: Content
# Management unreachable or 502/503/504 -> InfrastructureError, 401
# TOKEN_EXPIRED -> TokenExpiredError, any other error answer ->
# DownstreamError. The token provider raises InfrastructureError (Identity
# unreachable) or DownstreamError (Identity refused our credentials).
# TokenExpiredError is caught on purpose: it's our service token that
# expired, not the user's, so it must not reach the frontend as the user's
# TOKEN_EXPIRED.


class HttpTopicCatalog:
    def __init__(
        self, client: DownstreamClient, token_provider: ServiceTokenProvider
    ) -> None:
        self._client = client
        self._token_provider = token_provider

    def get_all(self) -> dict[str, Topic]:
        try:
            items = self._client.get_json(
                TOPICS_PATH, token=self._token_provider.get_token()
            )
            topics = [Topic(id=item["id"]) for item in items]
        except (
            InfrastructureError,
            DownstreamError,
            TokenExpiredError,
            ValueError,  # the body is not JSON
            KeyError,
            TypeError,
        ) as error:
            raise TopicCatalogUnavailableError() from error

        return {topic.id: topic for topic in topics}
