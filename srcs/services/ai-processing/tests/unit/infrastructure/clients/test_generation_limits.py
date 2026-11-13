import json

import httpx2 as httpx
import pytest
from shared_errors import InfrastructureError

from src.application.models.answer_validation_error import AnswerValidationError
from src.infrastructure.clients.OllamaSummarizerClient import (
    OllamaSummarizerClient, OllamaTopicSummary,
)


def ask(response, previous=None):
    requests = []
    def respond(request):
        requests.append(json.loads(request.content))
        return response
    with httpx.Client(base_url="http://ollama", transport=httpx.MockTransport(respond)) as client:
        result = OllamaSummarizerClient(client, "test", 120)._ask(
            "system", "input", OllamaTopicSummary, answer_name="summary",
            provider_error_name="summary", previous_failure=previous,
        )
    return result, requests


def valid_response():
    return httpx.Response(200, content=json.dumps({
        "message": {"content": '{"summary":"A complete summary."}'},
        "done": True, "done_reason": "stop",
    }) + "\n")


def test_generation_is_bounded():
    result, requests = ask(valid_response())
    assert result.summary == "A complete summary."
    assert requests[0]["options"]["num_predict"] == 512


def test_truncation_preserves_bounded_answer_for_shorter_retry():
    from src.application.models.generation_limit_error import GenerationLimitError
    response = httpx.Response(200, content=json.dumps({
        "message": {"content": "x" * 3000}, "done": True, "done_reason": "length",
    }) + "\n")
    with pytest.raises(GenerationLimitError) as caught:
        ask(response)
    assert len(caught.value.previous_answer) == 2000
    _, requests = ask(valid_response(), caught.value)
    assert requests[0]["options"]["num_predict"] == 256


def test_correction_explicitly_addresses_length_and_rejection():
    _, requests = ask(valid_response(), AnswerValidationError("too long", "{}"))
    instruction = requests[0]["messages"][-1]["content"]
    assert "120 characters" in instruction
    assert "If rejected=true, summary must be null" in instruction
