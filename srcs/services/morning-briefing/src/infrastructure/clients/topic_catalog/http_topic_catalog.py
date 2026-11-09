import httpx2 as httpx
from shared_auth import DownstreamError
from shared_errors import InfrastructureError

from src.application.exceptions import TopicCatalogUnavailableError
from src.domain.entities.topic import Topic
from src.infrastructure.clients.token_provider import TokenProvider

# Contract: docs/api/04_content-management.md, GET /internal/v1/topics.
# A bare array of topic objects. `summary` is read with .get(): Content
# Management only returns the ids until topic summaries exist (#167).
TOPICS_PATH = "/internal/v1/topics"
TIMEOUT_SECONDS = 2.0


class HttpTopicCatalog:
    def __init__(
        self,
        base_url: str,
        token_provider: TokenProvider,
        client: httpx.Client | None = None,
    ) -> None:
        self._token_provider = token_provider
        # `client` is a parameter so tests can pass a fake one.
        self._client = client or httpx.Client(base_url=base_url, timeout=TIMEOUT_SECONDS)

    def get_all(self) -> dict[str, Topic]:
        try:
            headers = {"Authorization": f"Bearer {self._token_provider.get_token()}"}
            response = self._client.get(TOPICS_PATH, headers=headers)
            response.raise_for_status()
            topics = [
                Topic(id=item["id"], summary=item.get("summary"))
                for item in response.json()
            ]
        except (
            httpx.HTTPError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
            InfrastructureError,  # Identity unreachable: no token
            DownstreamError,  # Identity refused our credentials
        ) as error:
            raise TopicCatalogUnavailableError() from error

        return {topic.id: topic for topic in topics}
