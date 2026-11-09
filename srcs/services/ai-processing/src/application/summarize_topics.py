from itertools import batched
from time import perf_counter

from src.application.ports.ai_summarizer import TopicSummarizerPort
from src.application.ports.content_management import TopicContentManagementPort
from src.domain.value_objects.summary import Summary

TOPIC_ARTICLE_LIMIT = 25  # Content Management's maximum page size.
TOPIC_SUMMARY_GROUP_SIZE = 4
EMPTY_TOPIC_SUMMARY = "Nothing special happened today, come back later"


class SummarizeTopics:
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
                self.content_management.save_topic_summary(
                    topic_id, EMPTY_TOPIC_SUMMARY, self.llm_model, 0
                )
                continue

            started_at = perf_counter()
            summary = self._combine(topic_id, summaries)
            generation_duration_ms = max(0, round((perf_counter() - started_at) * 1000))
            self.content_management.save_topic_summary(
                topic_id, summary, self.llm_model, generation_duration_ms
            )

    def _combine(self, topic_id: str, summaries: list[str]) -> str:
        while len(summaries) > 1:
            summaries = [
                self._summarize_group(topic_id, group)
                for group in batched(summaries, TOPIC_SUMMARY_GROUP_SIZE, strict=False)
            ]
        return summaries[0]

    def _summarize_group(self, topic_id: str, group: tuple[str, ...]) -> str:
        if len(group) == 1:
            return group[0]
        try:
            return Summary.from_text(
                self.ai_summarizer.ai_summarize_topic(topic_id, list(group))
            ).text
        except ValueError as exc:
            raise ValueError("Summarizer returned an invalid topic summary") from exc

    def _load_summaries(self, topic_id: str) -> list[str]:
        summaries_by_id: dict[str, str] = {}
        articles = self.content_management.list_topic_article_summaries(
            topic_id, TOPIC_ARTICLE_LIMIT
        )
        if len(articles) > TOPIC_ARTICLE_LIMIT:
            raise ValueError("Content Management returned too many topic articles")
        for article in articles:
            article_id = str(article.article_id)
            if article_id in summaries_by_id:
                raise ValueError("Content Management returned a duplicate article")
            try:
                summaries_by_id[article_id] = Summary.from_text(article.summary).text
            except ValueError as exc:
                raise ValueError(
                    "Content Management returned an invalid article summary"
                ) from exc

        return [summaries_by_id[key] for key in sorted(summaries_by_id)]
