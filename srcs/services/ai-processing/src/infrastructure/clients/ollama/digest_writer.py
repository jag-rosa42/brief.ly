import logging
from collections.abc import Generator

import httpx2
from pydantic import ValidationError
from shared_errors import InfrastructureError

from src.application.digest_prompt import Prompt
from src.infrastructure.clients.ollama.chat_format import (
    OllamaChatChunk,
    OllamaChatRequest,
    OllamaOptions,
    OllamaRequestMessage,
)

logger = logging.getLogger(__name__)

# A little variety reads better in a digest than the worker's temperature 0,
# which the worker needs for stable accept/reject decisions.
TEMPERATURE = 0.3
# Keep the model loaded between two readers' requests: loading it again takes
# seconds, which the reader would see as a long "Thinking...".
KEEP_ALIVE = "10m"
UNAVAILABLE = "The AI is unavailable right now."


class OllamaDigestWriter:
    """Streams the answer of Ollama's POST /api/chat, piece by piece.

    Ollama answers with one JSON object per line (NDJSON), each holding the
    next few characters of the answer, until one has "done": true. The
    worker's OllamaSummarizerClient (summarizer_client.py) reads the same
    stream but joins it into one JSON answer; here each piece is passed on as
    soon as it arrives.

    Stopping early is safe: when the reader leaves, the route stops asking
    for pieces and the generator is closed. Leaving the `with` block closes
    the connection, and Ollama stops generating.
    """

    def __init__(self, http_client: httpx2.Client, model: str, timeout_seconds: float):
        self._http_client = http_client
        self._model = model
        self._timeout_seconds = timeout_seconds

    def write(self, prompt: Prompt) -> Generator[str]:
        request = OllamaChatRequest(
            model=self._model,
            messages=[
                OllamaRequestMessage(role=message.role, content=message.content)
                for message in prompt.messages
            ],
            keep_alive=KEEP_ALIVE,
            options=OllamaOptions(temperature=TEMPERATURE, num_predict=prompt.max_tokens),
        )
        try:
            with self._http_client.stream(
                "POST", "/api/chat", json=request.to_json(), timeout=self._timeout_seconds
            ) as response:
                if response.is_error:
                    # Down, overloaded, or a wrong OLLAMA_MODEL (404): the
                    # reader can only try again later. The log says which.
                    logger.error("Ollama answered %s", response.status_code)
                    raise InfrastructureError(UNAVAILABLE)
                for line in response.iter_lines():
                    if not line:
                        continue
                    chunk = OllamaChatChunk.model_validate_json(line)
                    if chunk.error is not None:
                        raise InfrastructureError(UNAVAILABLE)
                    if chunk.message is not None and chunk.message.content:
                        yield chunk.message.content
                    if chunk.done:
                        # Never the reader's text: only how the answer ended.
                        logger.info(
                            "Ollama digest completed: done_reason=%s eval_count=%s",
                            chunk.done_reason,
                            chunk.eval_count,
                        )
                        return
        except httpx2.TransportError as exc:  # unreachable, or too slow
            raise InfrastructureError(UNAVAILABLE) from exc
        except ValidationError as exc:  # a line that is not Ollama's format
            raise InfrastructureError(UNAVAILABLE) from exc

        # The stream ended without "done": the answer was cut.
        raise InfrastructureError(UNAVAILABLE)
