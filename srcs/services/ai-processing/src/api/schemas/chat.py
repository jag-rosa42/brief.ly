"""Request body of the chat route (ADR-0011, docs/api/05_ai-processing.md).

Every field the reader controls is checked here, before anything else runs
(422 VALIDATION_ERROR otherwise). The typing rules are in text_rules.py.
"""

from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationInfo,
    field_validator,
    model_validator,
)

from src.api.schemas.text_rules import TYPED_TEXT_MESSAGE, answer_text, typed_text
from src.domain.value_objects.digest import (
    ANSWER_MAX_LENGTH,
    MAX_CHAT_MESSAGES,
    QUESTION_MAX_LENGTH,
    ChatMessage,
    ChatRole,
)


class ChatMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: ChatRole
    content: Annotated[str, StringConstraints(min_length=1, max_length=ANSWER_MAX_LENGTH)]

    @field_validator("content")
    @classmethod
    def check_content(cls, content: str, info: ValidationInfo) -> str:
        # `role` is declared first, so it is already validated here (absent
        # if it was invalid: its own error is reported then).
        if info.data.get("role") is ChatRole.USER:
            if len(content) > QUESTION_MAX_LENGTH:
                raise ValueError(
                    f"A question has at most {QUESTION_MAX_LENGTH} characters"
                )
            if not typed_text.fullmatch(content):
                raise ValueError(f"A question {TYPED_TEXT_MESSAGE}")
        elif not answer_text.fullmatch(content):
            raise ValueError("An answer must not contain control characters")
        return content

    def to_domain(self) -> ChatMessage:
        return ChatMessage(role=self.role, text=self.content)


class ChatRequest(BaseModel):
    """The whole conversation, ending with the reader's new question.

    The server doesn't remember past messages, so the browser sends them all
    with every question. They must come in this order:

        assistant: the digest
        user:      a question
        assistant: its answer
        ...
        user:      the new question
    """

    model_config = ConfigDict(extra="forbid")

    messages: Annotated[
        list[ChatMessageRequest],
        Field(min_length=2, max_length=MAX_CHAT_MESSAGES),
    ]

    @model_validator(mode="after")
    def check_turns(self) -> ChatRequest:
        for index, message in enumerate(self.messages):
            expected = ChatRole.ASSISTANT if index % 2 == 0 else ChatRole.USER
            if message.role is not expected:
                raise ValueError(
                    "Messages must start with the digest (assistant), then "
                    "alternate user and assistant, and end with a question (user)"
                )
        if self.messages[-1].role is not ChatRole.USER:
            raise ValueError("The last message must be the reader's question (user)")
        return self

    def to_domain(self) -> list[ChatMessage]:
        return [message.to_domain() for message in self.messages]
