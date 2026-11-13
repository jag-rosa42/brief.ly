from collections.abc import Generator

from shared_errors import InfrastructureError

from src.application.digest_prompt import Prompt
from src.application.exceptions import (
    ProfileReaderUnavailableError,
    TopicCatalogUnavailableError,
)


class FakeServiceTokenProvider:
    """Stands for shared_auth's ClientCredentialsTokenProvider: no Identity call.

    Gives `token`, or raises `error` when one is given (Identity down or
    refusing our credentials).
    """

    def __init__(
        self, token: str = "service-token", error: Exception | None = None
    ) -> None:
        self._token = token
        self._error = error

    def get_token(self) -> str:
        if self._error is not None:
            raise self._error
        return self._token


class FakeProfileReader:
    """Stands for Personalization: gives the followed topics, records the tokens."""

    def __init__(
        self,
        topic_ids: tuple[str, ...] = (),
        available: bool = True,
        error: Exception | None = None,
    ) -> None:
        self._topic_ids = topic_ids
        self._available = available
        # Raised as is: e.g. shared_auth's TokenExpiredError, which the real
        # client raises when Personalization answers 401 TOKEN_EXPIRED.
        self._error = error
        self.tokens: list[str] = []

    def get_topic_ids(self, user_token: str) -> tuple[str, ...]:
        self.tokens.append(user_token)
        if self._error is not None:
            raise self._error
        if not self._available:
            raise ProfileReaderUnavailableError()
        return self._topic_ids


class FakeTopicCatalog:
    """Stands for Content Management's topic list."""

    def __init__(
        self, summaries: dict[str, str | None] | None = None, available: bool = True
    ) -> None:
        self._summaries = summaries or {}
        self._available = available
        self.calls = 0

    def get_summaries(self) -> dict[str, str | None]:
        self.calls += 1
        if not self._available:
            raise TopicCatalogUnavailableError()
        return dict(self._summaries)


class FakeDigestWriter:
    """Stands for Ollama: records each prompt, streams `chunks`.

    With `fail_after`, it raises InfrastructureError after that many chunks,
    like Ollama stopping mid-answer. Lazy, like the real writer: nothing is
    recorded before the first chunk is asked for.
    """

    def __init__(
        self,
        chunks: tuple[str, ...] = ("Hello", " reader."),
        fail_after: int | None = None,
    ) -> None:
        self._chunks = chunks
        self._fail_after = fail_after
        self.prompts: list[Prompt] = []
        self.closed = False

    def write(self, prompt: Prompt) -> Generator[str]:
        self.prompts.append(prompt)
        try:
            for index, chunk in enumerate(self._chunks):
                if self._fail_after is not None and index >= self._fail_after:
                    raise InfrastructureError("The AI is unavailable right now.")
                yield chunk
        finally:
            self.closed = True
