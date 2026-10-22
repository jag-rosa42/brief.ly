import httpx2 as httpx

from src.application.exceptions import TopicCatalogUnavailableError
from src.domain.entities.topic import Topic

# Contract of Content Management's PR #140: GET /internal/v1/topics -> [{"id": str}]
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
            topics = [Topic(id=item["id"]) for item in response.json()]
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
            raise TopicCatalogUnavailableError() from error

        return {topic.id: topic for topic in topics}
