from src.application.ports.ai_summarizer import TopicSummarizerPort
from src.application.ports.content_management import TopicContentManagementPort


class SummarizeTopics:
    ARTICLE_LIMIT = 25
    SUMMARY_BATCH_SIZE = 4

    def __init__(
        self,
        content_management: TopicContentManagementPort,
        ai_summarizer: TopicSummarizerPort,
        llm_model: str,
    ) -> None:
        self.content_management = content_management
        self.ai_summarizer = ai_summarizer
        self.llm_model = llm_model

    def execute(self) -> None:
        topics = self.content_management.list_topics()
        if len(topics) != len(set(topics)):
            raise ValueError("Content Management returned duplicate topics")

        for topic_id in sorted(topics):
            summaries = self._load_summaries(topic_id)
            if not summaries:
                continue

            while len(summaries) > 1:
                next_level: list[str] = []
                for start in range(0, len(summaries), self.SUMMARY_BATCH_SIZE):
                    batch = summaries[start : start + self.SUMMARY_BATCH_SIZE]
                    if len(batch) == 1:
                        next_level.append(batch[0])
                    else:
                        summary = self.ai_summarizer.ai_summarize_topic(topic_id, batch)
                        if not 1 <= len(summary.strip()) <= 2000:
                            raise ValueError(
                                "Summarizer returned an invalid topic summary"
                            )
                        next_level.append(summary.strip())
                summaries = next_level

            self.content_management.save_topic_summary(
                topic_id, summaries[0], self.llm_model
            )

    def _load_summaries(self, topic_id: str) -> list[str]:
        summaries_by_id: dict[str, str] = {}
        articles = self.content_management.list_topic_article_summaries(
            topic_id, self.ARTICLE_LIMIT
        )
        if len(articles) > self.ARTICLE_LIMIT:
            raise ValueError("Content Management returned too many topic articles")
        for article in articles:
            article_id = str(article.article_id)
            if article_id in summaries_by_id:
                raise ValueError("Content Management returned a duplicate article")
            if (
                not isinstance(article.summary, str)
                or not 1 <= len(article.summary.strip()) <= 2000
            ):
                raise ValueError("Content Management returned an invalid article summary")
            summaries_by_id[article_id] = article.summary.strip()

        return [summaries_by_id[key] for key in sorted(summaries_by_id)]
