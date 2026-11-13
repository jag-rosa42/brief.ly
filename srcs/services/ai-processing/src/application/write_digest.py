from collections.abc import Iterator

from src.application.digest_prompt import build_chat_prompt, build_digest_prompt
from src.application.ports.digest_writer import DigestWriter
from src.application.ports.profile_reader import ProfileReader
from src.application.ports.topic_catalog import TopicCatalog
from src.domain.value_objects.digest import (
    NO_SUMMARIES_MESSAGE,
    NO_TOPICS_MESSAGE,
    ChatMessage,
    DigestLength,
    TopicNews,
)


class WriteDigest:
    """Write the reader's digest, or answer a follow-up question (ADR-0011).

    Both methods do their checks right away and return a lazy stream:
    - right away: read the profile and the topic summaries. A failure there
      raises before any answer is sent, so the route answers a plain 503;
    - lazily: call the LLM, piece by piece, while the route streams.

    The account always comes from the user's token, never from the request:
    a reader only ever gets their own topics.
    """

    def __init__(
        self,
        profile_reader: ProfileReader,
        topic_catalog: TopicCatalog,
        writer: DigestWriter,
    ) -> None:
        self._profile_reader = profile_reader
        self._topic_catalog = topic_catalog
        self._writer = writer

    def digest(self, user_token: str, length: DigestLength, focus: str) -> Iterator[str]:
        news, fixed_message = self._news(user_token)
        if fixed_message is not None:
            return iter([fixed_message])
        return self._writer.write(build_digest_prompt(news, length, focus))

    def answer(self, user_token: str, conversation: list[ChatMessage]) -> Iterator[str]:
        news, fixed_message = self._news(user_token)
        if fixed_message is not None:
            return iter([fixed_message])
        return self._writer.write(build_chat_prompt(news, conversation))

    def _news(self, user_token: str) -> tuple[list[TopicNews], str | None]:
        """The followed topics that have a summary, in the profile's order.

        Without any, the stream is a fixed message and the LLM is not called:
        it would have nothing true to say.
        """
        topic_ids = self._profile_reader.get_topic_ids(user_token)
        if not topic_ids:
            return [], NO_TOPICS_MESSAGE

        topics_summaries = self._topic_catalog.get_summaries()
        news: list[TopicNews] = []
        for topic_id in topic_ids:
            summary: str | None = topics_summaries.get(topic_id)
            # Skip a followed topic with no summary yet (None or "").
            if summary:
                news.append(TopicNews(topic_id=topic_id, summary=summary))
        if not news:
            return [], NO_SUMMARIES_MESSAGE
        return news, None
