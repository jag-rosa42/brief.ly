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
