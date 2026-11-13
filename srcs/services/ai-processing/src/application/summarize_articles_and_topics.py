import logging
from time import perf_counter
from typing import Protocol

logger = logging.getLogger(__name__)


class Executable(Protocol):
    def execute(self) -> None: ...


class SummarizeArticlesAndTopics:
    def __init__(
        self, summarize_articles: Executable, summarize_topics: Executable
    ) -> None:
        self.summarize_articles = summarize_articles
        self.summarize_topics = summarize_topics

    def execute(self) -> None:
        for phase, use_case in (
            ("articles", self.summarize_articles),
            ("topics", self.summarize_topics),
        ):
            started_at = perf_counter()
            succeeded = False
            logger.info("Starting worker phase=%s", phase)
            try:
                use_case.execute()
                succeeded = True
            finally:
                logger.info(
                    "Finished worker phase=%s succeeded=%s elapsed=%.2fs",
                    phase,
                    succeeded,
                    perf_counter() - started_at,
                )
