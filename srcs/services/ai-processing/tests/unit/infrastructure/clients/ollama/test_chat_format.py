"""Ollama's /api/chat request body (src/infrastructure/clients/ollama/chat_format.py)."""

from src.infrastructure.clients.ollama.chat_format import (
    OllamaChatRequest,
    OllamaOptions,
    OllamaRequestMessage,
)


def test_the_body_holds_only_the_fields_that_were_set() -> None:
    request = OllamaChatRequest(
        model="llama",
        messages=[OllamaRequestMessage(role="user", content="Hi")],
        options=OllamaOptions(temperature=0.3),
    )

    # No format, keep_alive, num_predict or num_ctx: Ollama's defaults apply.
    assert request.to_json() == {
        "model": "llama",
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": True,
        "options": {"temperature": 0.3},
    }


def test_the_optional_fields_are_sent_when_set() -> None:
    request = OllamaChatRequest(
        model="llama",
        messages=[OllamaRequestMessage(role="user", content="Hi")],
        format={"type": "object"},
        keep_alive="10m",
        options=OllamaOptions(temperature=0, num_predict=300, num_ctx=8192),
    )

    body = request.to_json()

    assert body["format"] == {"type": "object"}
    assert body["keep_alive"] == "10m"
    assert body["options"] == {"temperature": 0, "num_predict": 300, "num_ctx": 8192}
