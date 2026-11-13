import pytest

from src.application.exceptions import (
    ProfileReaderUnavailableError,
    TopicCatalogUnavailableError,
)
from src.application.write_digest import WriteDigest
from src.domain.value_objects.digest import (
    NO_SUMMARIES_MESSAGE,
    NO_TOPICS_MESSAGE,
    ChatMessage,
    ChatRole,
    DigestLength,
)
from tests.fakes import FakeDigestWriter, FakeProfileReader, FakeTopicCatalog

TOKEN = "user-token"
SUMMARIES: dict[str, str | None] = {
    "business": "Markets rose.",
    "science": "A probe reached Mars.",
    "health": None,
    "sports": "A final was won.",
}
QUESTION = [
    ChatMessage(ChatRole.ASSISTANT, "Your digest."),
    ChatMessage(ChatRole.USER, "And business?"),
]


def use_case(
    topic_ids: tuple[str, ...] = ("science", "business", "health"),
    writer: FakeDigestWriter | None = None,
) -> tuple[WriteDigest, FakeProfileReader, FakeDigestWriter]:
    reader = FakeProfileReader(topic_ids)
    writer = writer or FakeDigestWriter()
    return WriteDigest(reader, FakeTopicCatalog(SUMMARIES), writer), reader, writer


def test_digest_streams_the_writer_answer() -> None:
    write_digest, reader, writer = use_case()

    chunks = list(write_digest.digest(TOKEN, DigestLength.SHORT, "finance"))

    assert chunks == ["Hello", " reader."]
    assert reader.tokens == [TOKEN]
    assert len(writer.prompts) == 1


def test_digest_uses_followed_topics_with_a_summary_in_profile_order() -> None:
    write_digest, _, writer = use_case(("science", "business", "health"))

    list(write_digest.digest(TOKEN, DigestLength.SHORT, ""))

    news = writer.prompts[0].messages[1].content
    # Not "sports" (not followed), not "health" (no summary yet).
    assert news.index("name: science") < news.index("name: business")
    assert "name: sports" not in news
    assert "name: health" not in news


def test_digest_without_topics_is_a_fixed_message_without_the_llm() -> None:
    write_digest, _, writer = use_case(topic_ids=())

    assert list(write_digest.digest(TOKEN, DigestLength.SHORT, "")) == [NO_TOPICS_MESSAGE]
    assert writer.prompts == []


def test_digest_without_any_summary_is_a_fixed_message_without_the_llm() -> None:
    write_digest, _, writer = use_case(topic_ids=("health",))

    assert list(write_digest.digest(TOKEN, DigestLength.SHORT, "")) == [
        NO_SUMMARIES_MESSAGE
    ]
    assert writer.prompts == []


def test_answer_streams_the_writer_answer_from_the_conversation() -> None:
    write_digest, reader, writer = use_case()

    assert list(write_digest.answer(TOKEN, QUESTION)) == ["Hello", " reader."]
    assert reader.tokens == [TOKEN]
    assert writer.prompts[0].messages[-1].content == "<question>And business?</question>"


def test_answer_without_topics_is_a_fixed_message_without_the_llm() -> None:
    write_digest, _, writer = use_case(topic_ids=())

    assert list(write_digest.answer(TOKEN, QUESTION)) == [NO_TOPICS_MESSAGE]
    assert writer.prompts == []


def test_profile_and_topics_are_read_before_the_stream_starts() -> None:
    # Their errors must reach the route before it sends 200, to become a 503.
    write_digest = WriteDigest(
        FakeProfileReader(available=False), FakeTopicCatalog(), FakeDigestWriter()
    )
    with pytest.raises(ProfileReaderUnavailableError):
        write_digest.digest(TOKEN, DigestLength.SHORT, "")

    write_digest = WriteDigest(
        FakeProfileReader(("business",)),
        FakeTopicCatalog(available=False),
        FakeDigestWriter(),
    )
    with pytest.raises(TopicCatalogUnavailableError):
        write_digest.answer(TOKEN, QUESTION)


def test_the_llm_is_only_called_once_the_stream_is_read() -> None:
    write_digest, _, writer = use_case()

    chunks = write_digest.digest(TOKEN, DigestLength.SHORT, "")

    assert writer.prompts == []
    next(chunks)
    assert len(writer.prompts) == 1
