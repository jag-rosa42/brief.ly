from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

PUSHGATEWAY_ADDRESS = "pushgateway:9091"
PUSHGATEWAY_JOB = "ai_processing_summary"


class WorkerRunMetrics:
    def __init__(self) -> None:
        self.article_failures = 0
        self.topic_failures = 0
        self.registry = CollectorRegistry()
        self.completion = Gauge(
            "ai_worker_last_completion_timestamp_seconds",
            "Unix time of the last completed summary run",
            registry=self.registry,
        )
        self.success = Gauge(
            "ai_worker_last_run_success",
            "One when the last summary run had no failures",
            registry=self.registry,
        )
        self.duration = Gauge(
            "ai_worker_last_run_duration_seconds",
            "Duration of the last summary run in seconds",
            registry=self.registry,
        )
        self.article_failure_gauge = Gauge(
            "ai_worker_last_run_article_failures",
            "Article generation failures in the last summary run",
            registry=self.registry,
        )
        self.topic_failure_gauge = Gauge(
            "ai_worker_last_run_topic_failures",
            "Topic group generation failures in the last summary run",
            registry=self.registry,
        )

    def article_generation_failed(self) -> None:
        self.article_failures += 1

    def topic_group_generation_failed(self) -> None:
        self.topic_failures += 1

    def finish(self, *, completed_at: float, duration: float, fatal: bool) -> None:
        self.completion.set(completed_at)
        self.success.set(
            int(not fatal and not self.article_failures and not self.topic_failures)
        )
        self.duration.set(duration)
        self.article_failure_gauge.set(self.article_failures)
        self.topic_failure_gauge.set(self.topic_failures)


def publish_worker_metrics(registry: CollectorRegistry) -> None:
    push_to_gateway(PUSHGATEWAY_ADDRESS, job=PUSHGATEWAY_JOB, registry=registry)
