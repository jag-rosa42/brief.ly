"""Server-Sent Events (SSE): how the digest routes stream their answer.

SSE is a plain HTTP response (Content-Type: text/event-stream) that stays
open and carries events, each one a few "field: value" lines and a blank
line:

    event: chunk
    data: {"text": "Here is"}

    event: done
    data: {}

The status (200) and the headers leave before the first event, so an error
that happens later can't change the status any more: it becomes an `error`
event, with the usual {"error": {"code", "message"}} body. Errors found
before the stream starts (401, 422, 503) are ordinary JSON answers.
"""

import json
import logging
from collections.abc import Generator, Iterator
from typing import Final

from fastapi.responses import StreamingResponse
from shared_errors import InfrastructureError
from starlette.background import BackgroundTask

logger = logging.getLogger(__name__)

MEDIA_TYPE: Final[str] = "text/event-stream"
HEADERS: Final[dict[str, str]] = {
    # Every answer is new: no cache may keep or replay it.
    "Cache-Control": "no-store",
    # Ask any proxy (nginx-style) to pass events on at once, not in batches.
    "X-Accel-Buffering": "no",
}


class EventStream:
    """One streamed answer: the LLM's pieces sent as SSE events.

    A class because two parties share the LLM's stream: the generator that
    turns it into events, and the clean-up that closes it once the response
    is over. The object owns the stream, so both use the same one.
    """

    def __init__(self, chunks: Iterator[str]) -> None:
        self._chunks = chunks

    def events(self) -> Generator[str]:
        """The pieces of the answer as SSE events, ending with done or error."""
        try:
            for chunk in self._chunks:
                yield self._format("chunk", {"text": chunk})
        except InfrastructureError:
            logger.warning("Digest stream stopped: the LLM is unavailable", exc_info=True)
            yield self._error("SERVICE_UNAVAILABLE", "The AI is unavailable right now.")
            return
        except Exception:
            logger.exception("Digest stream failed")
            yield self._error("INTERNAL_SERVER_ERROR", "An unexpected error occurred.")
            return
        finally:
            self.close()

        yield self._format("done", {})

    def close(self) -> None:
        """Close the LLM's stream: a generator's close() runs its `finally` and
        leaves its `with` blocks, which closes the connection to Ollama, and
        Ollama stops generating. Closing a stream that already ended does
        nothing."""
        close = getattr(self._chunks, "close", None)
        if close is not None:
            close()

    def response(self) -> StreamingResponse:
        """The streamed answer, closed even when the reader leaves early.

        A sync iterator: Starlette reads it in its thread pool, one piece at a
        time, like the rest of this service's sync code. When the reader leaves
        (closes the tab, presses Stop), Starlette stops reading it but does not
        close it, so the LLM would go on writing for nobody. The background
        task runs once the response is over, in both cases, and closes it.
        """
        return StreamingResponse(
            self.events(),
            media_type=MEDIA_TYPE,
            headers=HEADERS,
            background=BackgroundTask(self.close),
        )

    @staticmethod
    def _format(name: str, data: object) -> str:
        # json.dumps escapes newlines, so `data` stays on one line as SSE needs.
        return f"event: {name}\ndata: {json.dumps(data)}\n\n"

    @classmethod
    def _error(cls, code: str, message: str) -> str:
        return cls._format("error", {"error": {"code": code, "message": message}})
