import httpx2 as httpx

from src.application.exceptions import TopicCatalogUnavailableError
from src.domain.entities.topic import Topic

# Contract: docs/api/04_content-management.md, GET /internal/v1/topics.
# A bare array of topic objects. `summary` is read with .get(): Content
# Management only returns the ids until topic summaries exist (#167).
TOPICS_PATH = "/internal/v1/topics"
TIMEOUT_SECONDS = 2.0


class HttpTopicCatalog:
    def __init__(self, base_url: str, client: httpx.Client | None = None) -> None:
        # `client` is a parameter so tests can pass a fake one.
        self._client = client or httpx.Client(base_url=base_url, timeout=TIMEOUT_SECONDS)

    def get_all(self) -> dict[str, Topic]:
        try:
            # TODO(service-token): CM will require a service token on /internal/*.
            # When shared_auth's service-token provider exists, add the header here:
            #   headers={"Authorization": f"Bearer {token_provider.get_token()}"}
            # The provider caches the token and renews it before it expires.
            response = self._client.get(TOPICS_PATH)
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
        ) as error:
            raise TopicCatalogUnavailableError() from error

        return {topic.id: topic for topic in topics}
