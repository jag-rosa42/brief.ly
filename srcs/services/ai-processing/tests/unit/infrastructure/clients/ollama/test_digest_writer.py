import json
from collections.abc import Callable, Iterator

import httpx2 as httpx
import pytest
from shared_errors import InfrastructureError

from src.application.digest_prompt import Prompt, PromptMessage
from src.infrastructure.clients.ollama.digest_writer import (
    KEEP_ALIVE,
    TEMPERATURE,
    OllamaDigestWriter,
)
from tests.model import DEFAULT_MODEL

PROMPT = Prompt(
    messages=(PromptMessage("system", "Rules."), PromptMessage("user", "News.")),
    max_tokens=250,
)


def line(content: str = "", done: bool = False, **extra: object) -> bytes:
    return (
        json.dumps({"message": {"content": content}, "done": done, **extra}) + "\n"
    ).encode()


def writer(handler: Callable[[httpx.Request], httpx.Response]) -> OllamaDigestWriter:
    client = httpx.Client(
        base_url="http://ollama:11434", transport=httpx.MockTransport(handler)
    )
    return OllamaDigestWriter(client, DEFAULT_MODEL, timeout_seconds=5)


def test_write_streams_each_piece_of_the_answer() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/chat"
        body = json.loads(request.content)
        assert body == {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": "Rules."},
                {"role": "user", "content": "News."},
            ],
            "stream": True,
            "keep_alive": KEEP_ALIVE,
            "options": {"temperature": TEMPERATURE, "num_predict": 250},
        }
        return httpx.Response(
            200,
            content=line("Markets")
            + line(" rose.")
            + b"\n"
            + line(done=True, done_reason="stop"),
        )

    assert list(writer(respond).write(PROMPT)) == ["Markets", " rose."]


def test_write_sends_nothing_before_the_first_piece_is_read() -> None:
    calls: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, content=line("Hi", done=True))

    chunks = writer(respond).write(PROMPT)

    assert calls == []
    assert list(chunks) == ["Hi"]
    assert len(calls) == 1


@pytest.mark.parametrize("status", [404, 500, 502, 503, 504])
def test_write_raises_infrastructure_error_on_an_error_status(status: int) -> None:
    chunks = writer(lambda _request: httpx.Response(status)).write(PROMPT)

    with pytest.raises(InfrastructureError):
        list(chunks)


def test_write_raises_infrastructure_error_when_ollama_is_unreachable() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(InfrastructureError):
        list(writer(respond).write(PROMPT))


def test_write_raises_infrastructure_error_when_ollama_fails_mid_answer() -> None:
    def respond(_request: httpx.Request) -> httpx.Response:
        failure = b'{"error": "out of memory"}\n'
        return httpx.Response(200, content=line("Markets") + failure)

    chunks = writer(respond).write(PROMPT)

    assert next(chunks) == "Markets"
    with pytest.raises(InfrastructureError):
        next(chunks)


def test_write_raises_infrastructure_error_on_a_line_in_another_format() -> None:
    def respond(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json\n")

    with pytest.raises(InfrastructureError):
        list(writer(respond).write(PROMPT))


def test_write_raises_infrastructure_error_when_the_stream_ends_without_done() -> None:
    def respond(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=line("Markets"))

    chunks = writer(respond).write(PROMPT)

    assert next(chunks) == "Markets"
    with pytest.raises(InfrastructureError):
        next(chunks)


def test_closing_the_stream_early_closes_the_response() -> None:
    closed: list[bool] = []

    class TrackedStream(httpx.SyncByteStream):
        def __iter__(self) -> Iterator[bytes]:
            yield line("one")
            yield line("two")
            yield line(done=True)

        def close(self) -> None:
            closed.append(True)

    chunks = writer(lambda _request: httpx.Response(200, stream=TrackedStream())).write(
        PROMPT
    )

    assert next(chunks) == "one"
    chunks.close()  # what happens when the reader leaves

    assert closed == [True]
