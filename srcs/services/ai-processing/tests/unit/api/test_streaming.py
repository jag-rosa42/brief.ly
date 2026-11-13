"""The Server-Sent Events of the digest routes (src/api/streaming.py, EventStream)."""

import asyncio
from collections.abc import Iterator

from shared_errors import InfrastructureError

from src.api.streaming import EventStream


def events(chunks: Iterator[str]) -> list[str]:
    return list(EventStream(chunks).events())


def test_each_piece_is_a_chunk_event_then_done() -> None:
    assert events(iter(["Hi", ' "reader"\n'])) == [
        'event: chunk\ndata: {"text": "Hi"}\n\n',
        # Quotes and newlines are escaped by JSON: `data` stays one line.
        'event: chunk\ndata: {"text": " \\"reader\\"\\n"}\n\n',
        "event: done\ndata: {}\n\n",
    ]


def test_an_llm_failure_mid_answer_ends_with_an_error_event() -> None:
    def chunks() -> Iterator[str]:
        yield "Hi"
        raise InfrastructureError("Ollama is unavailable.")

    assert events(chunks()) == [
        'event: chunk\ndata: {"text": "Hi"}\n\n',
        "event: error\n"
        'data: {"error": {"code": "SERVICE_UNAVAILABLE", '
        '"message": "The AI is unavailable right now."}}\n\n',
    ]


def test_an_unexpected_failure_hides_its_details() -> None:
    def chunks() -> Iterator[str]:
        raise RuntimeError("secret internal detail")
        yield ""  # makes this function a generator

    (event,) = events(chunks())

    assert "INTERNAL_SERVER_ERROR" in event
    assert "secret" not in event


def test_stopping_early_closes_the_llm_stream() -> None:
    closed: list[bool] = []

    def chunks() -> Iterator[str]:
        try:
            yield "one"
            yield "two"
        finally:
            closed.append(True)

    stream = EventStream(chunks()).events()
    next(stream)
    stream.close()  # what Starlette's clean-up does when the reader leaves

    assert closed == [True]


def test_the_response_closes_the_llm_stream_once_over() -> None:
    # The reader left mid-answer: Starlette stops reading the events without
    # closing them, then runs the response's background task.
    closed: list[bool] = []

    def chunks() -> Iterator[str]:
        try:
            yield "one"
            yield "two"
        finally:
            closed.append(True)

    llm_stream = chunks()
    response = EventStream(llm_stream).response()
    next(llm_stream)  # the answer has started
    assert response.background is not None

    asyncio.run(response.background())

    assert closed == [True]
