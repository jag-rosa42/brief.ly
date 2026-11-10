import logging
from contextlib import closing

from httpx2 import Client
from shared_auth import ClientCredentialsTokenProvider

from src.application.summarize_articles_and_topics import SummarizeArticlesAndTopics
from src.application.summarize_topics import SummarizeTopics
from src.application.SummarizeArticles import SummarizeArticles
from src.infrastructure.clients.ContentManagementClient import ContentManagementClient
from src.infrastructure.clients.OllamaSummarizerClient import OllamaSummarizerClient
from src.infrastructure.clients.token_provider import TokenProvider
from src.infrastructure.config.service_token import ServiceTokenSettings
from src.infrastructure.config.worker import WorkerSettings

# Contract: docs/api/06_service-to-service.md. The client ID, audience and
# scopes must match this service's entry in Identity's registry
# (identity/src/infrastructure/oauth/service_clients.py).
TOKEN_PATH = "/internal/v1/oauth/token"
CLIENT_ID = "ai-processing"
CONTENT_MANAGEMENT_AUDIENCE = "transcendence:content-management"
CONTENT_MANAGEMENT_SCOPES = ("topics:read", "articles:read", "summaries:write")


def run_worker(
    settings: WorkerSettings,
    content_http_client: Client,
    ollama_http_client: Client,
    token_provider: TokenProvider,
) -> None:
    content_management = ContentManagementClient(content_http_client, token_provider)
    summarizer = OllamaSummarizerClient(
        ollama_http_client,
        settings.OLLAMA_MODEL,
        settings.OLLAMA_TIMEOUT_SECONDS,
    )
    SummarizeArticlesAndTopics(
        SummarizeArticles(
            content_management,
            summarizer,
            settings.OLLAMA_MODEL,
            batch_size=settings.ARTICLE_BATCH_SIZE,
        ),
        SummarizeTopics(content_management, summarizer, settings.OLLAMA_MODEL),
    ).execute()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = WorkerSettings()
    token_settings = ServiceTokenSettings()
    # One provider for the whole run: it caches the token and renews it if
    # the run outlasts it. closing() calls its close() at the end, like the
    # `with` closes the two HTTP clients.
    token_provider = ClientCredentialsTokenProvider(
        issuer_service="identity",
        token_endpoint_url=f"{token_settings.IDENTITY_URL}{TOKEN_PATH}",
        client_id=CLIENT_ID,
        client_secret=token_settings.AI_PROCESSING_CLIENT_SECRET,
        audience=CONTENT_MANAGEMENT_AUDIENCE,
        scopes=CONTENT_MANAGEMENT_SCOPES,
    )
    with (
        closing(token_provider),
        Client(base_url=settings.CONTENT_MANAGEMENT_BASE_URL) as content_http_client,
        Client(base_url=settings.OLLAMA_BASE_URL) as ollama_http_client,
    ):
        run_worker(settings, content_http_client, ollama_http_client, token_provider)


if __name__ == "__main__":
    main()
