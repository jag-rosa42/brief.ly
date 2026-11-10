import time
from typing import Literal

from prometheus_client import Counter, Gauge

IngestionOutcome = Literal["succeeded", "partial", "failed"]

INGESTION_RUNS = Counter(
    "content_ingestion_runs_total",
    "Completed Content Management ingestion runs.",
    ["outcome"],
)
ARTICLES_CREATED = Counter(
    "content_ingestion_articles_created_total",
    "Articles stored during Content Management ingestion.",
)
INGESTION_FAILURES = Counter(
    "content_ingestion_failures_total",
    "Source discovery and article processing failures reported by ingestion.",
)
LAST_COMPLETION = Gauge(
    "content_ingestion_last_completion_timestamp_seconds",
    "Unix time of the last completed Content Management ingestion run.",
)


def record_ingestion_run(
    outcome: IngestionOutcome,
    *,
    articles_created: int = 0,
    failures: int = 0,
) -> None:
    INGESTION_RUNS.labels(outcome=outcome).inc()
    if articles_created:
        ARTICLES_CREATED.inc(articles_created)
    if failures:
        INGESTION_FAILURES.inc(failures)
    LAST_COMPLETION.set(time.time())
