from src.infrastructure.config.worker import WorkerSettings

DEFAULT_MODEL = WorkerSettings().OLLAMA_MODEL


class RecordingFailureMetrics:
    def __init__(self) -> None:
        self.article_failures = 0
        self.topic_failures = 0

    def article_generation_failed(self) -> None:
        self.article_failures += 1

    def topic_group_generation_failed(self) -> None:
        self.topic_failures += 1

    def article_summary_succeeded(self, duration_seconds: float) -> None:
        pass
