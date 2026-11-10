import logging
from contextlib import closing

from httpx2 import Client
from shared_auth import ClientCredentialsTokenProvider, DownstreamClient

from src.application.summarize_articles_and_topics import SummarizeArticlesAndTopics
from src.application.summarize_topics import SummarizeTopics
from src.application.SummarizeArticles import SummarizeArticles
from src.infrastructure.clients.content_management import CONTENT_MANAGEMENT_SERVICE
from src.infrastructure.clients.ContentManagementClient import ContentManagementClient
from src.infrastructure.clients.OllamaSummarizerClient import OllamaSummarizerClient
from src.infrastructure.clients.service_token_provider import ServiceTokenProvider
from src.infrastructure.config.service_client import (
    CLIENT_ID,
    CONTENT_MANAGEMENT_AUDIENCE,
    CONTENT_MANAGEMENT_SCOPES,
    TOKEN_PATH,
    ServiceClientSettings,
)
from src.infrastructure.config.worker import WorkerSettings

# Longer than DownstreamClient's 5 s: the worker has no user waiting.
CONTENT_MANAGEMENT_TIMEOUT_SECONDS = 10.0


def run_worker(
    settings: WorkerSettings,
    content_http_client: DownstreamClient,
    ollama_http_client: Client,
    token_provider: ServiceTokenProvider,
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
    client_settings = ServiceClientSettings()
    # One provider for the whole run: it caches the token and renews it if
    # the run outlasts it. closing() calls close() at the end, for it and the
    # Content Management client, like the `with` closes the Ollama client.
    token_provider = ClientCredentialsTokenProvider(
        issuer_service="identity",
        token_endpoint_url=f"{client_settings.IDENTITY_URL}{TOKEN_PATH}",
        client_id=CLIENT_ID,
        client_secret=client_settings.AI_PROCESSING_CLIENT_SECRET,
        audience=CONTENT_MANAGEMENT_AUDIENCE,
        scopes=CONTENT_MANAGEMENT_SCOPES,
    )
    with (
        closing(token_provider),
        closing(
            DownstreamClient(
                CONTENT_MANAGEMENT_SERVICE,
                settings.CONTENT_MANAGEMENT_BASE_URL,
                timeout=CONTENT_MANAGEMENT_TIMEOUT_SECONDS,
            )
        ) as content_http_client,
        Client(base_url=settings.OLLAMA_BASE_URL) as ollama_http_client,
    ):
        run_worker(settings, content_http_client, ollama_http_client, token_provider)


if __name__ == "__main__":
    main()
