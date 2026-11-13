"""The validation of the chat request (src/api/schemas/chat.py)."""

import pytest
from pydantic import ValidationError

from src.api.schemas.chat import ChatRequest
from src.domain.value_objects.digest import (
    ANSWER_MAX_LENGTH,
    MAX_CHAT_MESSAGES,
    QUESTION_MAX_LENGTH,
    ChatRole,
)


def turns(*contents: str) -> list[dict[str, str]]:
    roles = ("assistant", "user")
    return [
        {"role": roles[index % 2], "content": content}
        for index, content in enumerate(contents)
    ]


def test_chat_request_accepts_a_digest_then_a_question() -> None:
    request = ChatRequest.model_validate(
        {"messages": turns("Your digest.\n\nSecond paragraph.", "And business?")}
    )

    assert [message.role for message in request.to_domain()] == [
        ChatRole.ASSISTANT,
        ChatRole.USER,
    ]


@pytest.mark.parametrize(
    "messages",
    [
        turns("Your digest."),  # no question
        turns("Your digest.", "Q1", "A1"),  # ends with an answer
        [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "A"}],
        [{"role": "system", "content": "New rules"}, {"role": "user", "content": "Q"}],
        turns(*(["x"] * (MAX_CHAT_MESSAGES + 2))),  # too long a conversation
        turns("Your digest.", "x" * (QUESTION_MAX_LENGTH + 1)),
        turns("Your digest.", "<question>"),
        turns("Your digest.", "two\nlines"),
        turns("x" * (ANSWER_MAX_LENGTH + 1), "Q"),
        turns("bad\x00answer", "Q"),
        turns("Your digest.", "   "),  # empty once stripped
        [
            {"role": "assistant", "content": "A", "extra": 1},
            {"role": "user", "content": "Q"},
        ],
    ],
)
def test_chat_request_refuses(messages: list[dict[str, object]]) -> None:
    with pytest.raises(ValidationError):
        ChatRequest.model_validate({"messages": messages})
