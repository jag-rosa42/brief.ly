from typing import Protocol


class FailureMetricsPort(Protocol):
    def article_generation_failed(self) -> None: ...

    def topic_group_generation_failed(self) -> None: ...
