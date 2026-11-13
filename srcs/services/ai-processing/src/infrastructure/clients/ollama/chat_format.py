"""Ollama's POST /api/chat format, both directions (https://docs.ollama.com/api/chat).

Shared by the worker's summarizer_client.py and the digest's digest_writer.py.
Pydantic models rather than plain dictionaries: a misspelled field or a
wrong type is an error here, not a request Ollama silently misreads.
"""

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# What we send
# ---------------------------------------------------------------------------


class OllamaRequestMessage(BaseModel):
    role: str  # "system", "user" or "assistant"
    content: str


class OllamaOptions(BaseModel):
    temperature: float
    # The most tokens the model may write. None: Ollama's default.
    num_predict: int | None = None
    # The context window, in tokens (prompt + answer). None: Ollama's default.
    num_ctx: int | None = None


class OllamaChatRequest(BaseModel):
    model: str
    messages: list[OllamaRequestMessage]
    # Always streamed: Ollama sends the answer a few characters at a time.
    stream: bool = True
    # A JSON schema the answer must follow (the worker's structured answers).
    format: dict[str, object] | None = None
    # How long Ollama keeps the model loaded after answering, e.g. "10m".
    keep_alive: str | None = None
    options: OllamaOptions

    def to_json(self) -> dict[str, object]:
        """The JSON body. Fields left at None are not sent: Ollama's defaults apply."""
        return self.model_dump(exclude_none=True)


# ---------------------------------------------------------------------------
# What Ollama streams back: one JSON object per line (NDJSON)
# ---------------------------------------------------------------------------


class OllamaChatMessage(BaseModel):
    content: str = ""


class OllamaChatChunk(BaseModel):
    """One line of Ollama's streamed /api/chat response."""

    model_config = ConfigDict(extra="ignore")

    message: OllamaChatMessage | None = None
    done: bool = False
    done_reason: str | None = None
    eval_count: int | None = None
    error: str | None = None
