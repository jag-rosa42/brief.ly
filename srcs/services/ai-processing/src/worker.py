import logging
from collections.abc import Callable
from time import perf_counter, time

from httpx2 import Client
from prometheus_client import CollectorRegistry

from src.application.summarize_articles_and_topics import SummarizeArticlesAndTopics
from src.application.summarize_topics import SummarizeTopics
from src.application.SummarizeArticles import SummarizeArticles
from src.infrastructure.clients.ContentManagementClient import ContentManagementClient
from src.infrastructure.clients.OllamaSummarizerClient import OllamaSummarizerClient
from src.infrastructure.config.worker import WorkerSettings
from src.infrastructure.metrics.worker import WorkerRunMetrics, publish_worker_metrics

logger = logging.getLogger(__name__)


def run_worker(
    settings: WorkerSettings,
    content_http_client: Client,
    ollama_http_client: Client,
    publish: Callable[[CollectorRegistry], None] = publish_worker_metrics,
) -> None:
    metrics = WorkerRunMetrics()
    started_at = perf_counter()
    fatal = True
    try:
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
                failure_metrics=metrics,
            ),
            SummarizeTopics(
                content_management, summarizer, settings.OLLAMA_MODEL, metrics
            ),
        ).execute()
        fatal = False
    finally:
        metrics.finish(
            completed_at=time(), duration=max(0, perf_counter() - started_at), fatal=fatal
        )
        try:
            publish(metrics.registry)
        except Exception:
            logger.exception("Failed to push AI worker metrics to Pushgateway")


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
