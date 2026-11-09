import re
from uuid import UUID

import pytest

from src.application.models.topic_article_summary import (
    TopicArticleSummary,
)
from src.application.summarize_articles_and_topics import SummarizeArticlesAndTopics
from src.application.summarize_topics import EMPTY_TOPIC_SUMMARY, SummarizeTopics
from tests.model import DEFAULT_MODEL


def article_summary(number: int) -> TopicArticleSummary:
    return TopicArticleSummary(UUID(int=number), f"summary-{number}")


def test_reads_one_list_and_combines_summaries_in_bounded_groups(monkeypatch) -> None:
    times = iter((10.0, 10.1234))
    monkeypatch.setattr(
        "src.application.summarize_topics.perf_counter", lambda: next(times)
    )

    class ContentManagement:
        def __init__(self) -> None:
            self.reads: list[tuple[str, int]] = []
            self.writes: list[tuple[str, str, str, int]] = []

        def list_topics(self) -> list[str]:
            return ["technology", "science"]

        def list_topic_article_summaries(
            self, topic_id: str, limit: int
        ) -> list[TopicArticleSummary]:
            self.reads.append((topic_id, limit))
            if topic_id == "science":
                return []
            return [article_summary(number) for number in (5, 2, 1, 4, 3)]

        def save_topic_summary(
            self, topic_id: str, summary: str, llm_model: str, generation_duration_ms: int
        ) -> None:
            self.writes.append((topic_id, summary, llm_model, generation_duration_ms))

    class Summarizer:
        def __init__(self) -> None:
            self.inputs: list[tuple[str, list[str]]] = []

        def ai_summarize_topic(self, topic_id: str, summaries: list[str]) -> str:
            assert 2 <= len(summaries) <= 4
            self.inputs.append((topic_id, summaries))
            return "[" + "|".join(summaries) + "]"

    content_management = ContentManagement()
    summarizer = Summarizer()
    SummarizeTopics(content_management, summarizer, DEFAULT_MODEL).execute()

    assert content_management.reads == [
        ("science", 25),
        ("technology", 25),
    ]
    assert summarizer.inputs == [
        ("technology", ["summary-1", "summary-2", "summary-3", "summary-4"]),
        ("technology", ["[summary-1|summary-2|summary-3|summary-4]", "summary-5"]),
    ]
    assert content_management.writes == [
        ("science", EMPTY_TOPIC_SUMMARY, DEFAULT_MODEL, 0),
        (
            "technology",
            "[[summary-1|summary-2|summary-3|summary-4]|summary-5]",
            DEFAULT_MODEL,
            123,
        ),
    ]


def test_duplicate_article_stops_before_topic_write() -> None:
    class ContentManagement:
        def __init__(self) -> None:
            self.calls = 0
            self.written = False

        def list_topics(self) -> list[str]:
            return ["technology"]

        def list_topic_article_summaries(
            self, topic_id: str, limit: int
        ) -> list[TopicArticleSummary]:
            self.calls += 1
            return [article_summary(1), article_summary(1)]

        def save_topic_summary(
            self, topic_id: str, summary: str, llm_model: str, generation_duration_ms: int
        ) -> None:
            self.written = True

    class Summarizer:
        def ai_summarize_topic(self, topic_id: str, summaries: list[str]) -> str:
            raise AssertionError("Incomplete topic must not be summarized")

    content_management = ContentManagement()
    with pytest.raises(ValueError, match="duplicate article"):
        SummarizeTopics(content_management, Summarizer(), DEFAULT_MODEL).execute()

    assert content_management.written is False


def test_topic_with_25_articles_uses_one_read() -> None:
    class ContentManagement:
        def __init__(self) -> None:
            self.written: str | None = None
            self.reads = 0

        def list_topics(self) -> list[str]:
            return ["technology"]

        def list_topic_article_summaries(
            self, topic_id: str, limit: int
        ) -> list[TopicArticleSummary]:
            self.reads += 1
            assert limit == 25
            return [article_summary(number) for number in range(1, 26)]

        def save_topic_summary(
            self, topic_id: str, summary: str, llm_model: str, generation_duration_ms: int
        ) -> None:
            self.written = summary

    class Summarizer:
        def ai_summarize_topic(self, topic_id: str, summaries: list[str]) -> str:
            return " | ".join(summaries)

    content_management = ContentManagement()
    SummarizeTopics(content_management, Summarizer(), DEFAULT_MODEL).execute()

    assert content_management.reads == 1
    assert re.findall(r"summary-\d+", content_management.written or "") == [
        f"summary-{number}" for number in range(1, 26)
    ]


def test_missing_article_summary_stops_before_topic_write() -> None:
    class ContentManagement:
        written = False

        def list_topics(self) -> list[str]:
            return ["technology"]

        def list_topic_article_summaries(
            self, topic_id: str, limit: int
        ) -> list[TopicArticleSummary]:
            return [TopicArticleSummary(UUID(int=1), None)]

        def save_topic_summary(
            self, topic_id: str, summary: str, llm_model: str, generation_duration_ms: int
        ) -> None:
            self.written = True

    class Summarizer:
        def ai_summarize_topic(self, topic_id: str, summaries: list[str]) -> str:
            raise AssertionError("Invalid input must not be summarized")

    content_management = ContentManagement()
    with pytest.raises(ValueError, match="invalid article summary"):
        SummarizeTopics(content_management, Summarizer(), DEFAULT_MODEL).execute()
    assert content_management.written is False


def test_failed_article_phase_prevents_topic_phase() -> None:
    class Articles:
        def execute(self) -> None:
            raise RuntimeError("article write failed")

    class Topics:
        def execute(self) -> None:
            raise AssertionError("Topic phase must wait for articles")

    with pytest.raises(RuntimeError, match="article write failed"):
        SummarizeArticlesAndTopics(Articles(), Topics()).execute()


@pytest.mark.parametrize(
    "failure", [RuntimeError("Ollama unavailable"), ValueError("invalid summary")]
)
def test_first_generation_failure_saves_article_summary_and_continues(
    failure: Exception,
) -> None:
    class ContentManagement:
        def __init__(self) -> None:
            self.writes: list[tuple[str, str]] = []

        def list_topics(self) -> list[str]:
            return ["science", "technology"]

        def list_topic_article_summaries(
            self, topic_id: str, limit: int
        ) -> list[TopicArticleSummary]:
            return [article_summary(1), article_summary(2)]

        def save_topic_summary(
            self, topic_id: str, summary: str, llm_model: str, generation_duration_ms: int
        ) -> None:
            self.writes.append((topic_id, summary))

    class Summarizer:
        def ai_summarize_topic(self, topic_id: str, summaries: list[str]) -> str:
            if topic_id == "science":
                raise failure
            return "Combined summary"

    content_management = ContentManagement()
    SummarizeTopics(content_management, Summarizer(), DEFAULT_MODEL).execute()

    assert content_management.writes == [
        ("science", "summary-1"),
        ("technology", "Combined summary"),
    ]


def test_later_generation_failure_saves_completed_group_and_continues() -> None:
    class ContentManagement:
        def __init__(self) -> None:
            self.writes: list[tuple[str, str]] = []

        def list_topics(self) -> list[str]:
            return ["science", "technology"]

        def list_topic_article_summaries(
            self, topic_id: str, limit: int
        ) -> list[TopicArticleSummary]:
            return [article_summary(number) for number in range(1, 9)]

        def save_topic_summary(
            self, topic_id: str, summary: str, llm_model: str, generation_duration_ms: int
        ) -> None:
            self.writes.append((topic_id, summary))

    class Summarizer:
        def ai_summarize_topic(self, topic_id: str, summaries: list[str]) -> str:
            if topic_id == "science" and summaries[0] == "summary-5":
                raise RuntimeError("Ollama unavailable")
            return " + ".join(summaries)

    content_management = ContentManagement()
    SummarizeTopics(content_management, Summarizer(), DEFAULT_MODEL).execute()

    assert content_management.writes == [
        ("science", "summary-1 + summary-2 + summary-3 + summary-4"),
        (
            "technology",
            "summary-1 + summary-2 + summary-3 + summary-4 + "
            "summary-5 + summary-6 + summary-7 + summary-8",
        ),
    ]
