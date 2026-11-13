"""The digest and its follow-up chat (ADR-0011): what a reader may ask for.

The limits live here, in one place: the API schema checks them on every
request, and the frontend repeats them (srcs/frontend/src/features/digest/
types.ts) so the user sees the error before sending.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

# The reader's optional focus ("what matters for someone in finance").
FOCUS_MAX_LENGTH: Final[int] = 200
# One follow-up question.
QUESTION_MAX_LENGTH: Final[int] = 500
# One earlier answer sent back by the browser. A detailed digest is about
# 1,500 characters; the margin covers longer answers.
ANSWER_MAX_LENGTH: Final[int] = 4000
# The whole conversation sent with a question: the digest, then questions and
# answers, the new question last. Older turns are dropped by the browser.
MAX_CHAT_MESSAGES: Final[int] = 10

# Streamed instead of an AI answer, without calling the LLM.
NO_TOPICS_MESSAGE: Final[str] = (
    "Follow some topics first: your digest is written from the news of the "
    "topics you follow. Choose them on your profile page."
)
NO_SUMMARIES_MESSAGE: Final[str] = (
    "Your topics have no summary yet today. Come back once today's news has "
    "been summarized."
)


class DigestLength(StrEnum):
    SHORT = "short"
    DETAILED = "detailed"


class ChatRole(StrEnum):
    # The reader's questions.
    USER = "user"
    # The AI's earlier answers, the digest first.
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class ChatMessage:
    role: ChatRole
    text: str


@dataclass(frozen=True)
class TopicNews:
    """One followed topic and its latest summary, as Content Management stores it."""

    topic_id: str
    summary: str
