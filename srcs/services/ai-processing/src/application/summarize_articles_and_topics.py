from typing import Protocol


class Executable(Protocol):
    def execute(self) -> None: ...


class SummarizeArticlesAndTopics:
    def __init__(
        self, summarize_articles: Executable, summarize_topics: Executable
    ) -> None:
        self.summarize_articles = summarize_articles
        self.summarize_topics = summarize_topics

    def execute(self) -> None:
        self.summarize_articles.execute()
        self.summarize_topics.execute()
