import logging

from httpx2 import Client

from src.application.summarize_articles_and_topics import SummarizeArticlesAndTopics
from src.application.summarize_topics import SummarizeTopics
from src.application.SummarizeArticles import SummarizeArticles
from src.infrastructure.clients.ContentManagementClient import ContentManagementClient
from src.infrastructure.clients.OllamaSummarizerClient import OllamaSummarizerClient
from src.infrastructure.config.worker import WorkerSettings


def run_worker(
    settings: WorkerSettings,
    content_http_client: Client,
    ollama_http_client: Client,
) -> None:
    content_management = ContentManagementClient(content_http_client)
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
    with (
        Client(base_url=settings.CONTENT_MANAGEMENT_BASE_URL) as content_http_client,
        Client(base_url=settings.OLLAMA_BASE_URL) as ollama_http_client,
    ):
        run_worker(settings, content_http_client, ollama_http_client)


if __name__ == "__main__":
    main()
