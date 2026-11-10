"""Run one article through the worker with fake Content Management and real Ollama.

From the ai-processing container in the VM:
    python -m scripts.try_ollama_workflow
"""

import argparse
import json
from contextlib import closing
from dataclasses import dataclass
from uuid import UUID

import httpx2 as httpx
from shared_auth import DownstreamClient

from src.infrastructure.config.worker import WorkerSettings
from src.worker import run_worker

ARTICLE_ID = UUID("123e4567-e89b-12d3-a456-426614174030")
TOPIC_ID = "technology"
DEFAULT_OLLAMA_URL = "http://10.0.2.2:11434"
DEFAULT_MODEL = WorkerSettings().OLLAMA_MODEL


class StaticTokenProvider:
    """A fixed service token: Content Management is faked here, so no Identity."""

    def get_token(self) -> str:
        return "service-token"


ARTICLE_SOURCE_URL = "https://openai.com/index/gpt-4o-and-more-tools-to-chatgpt-free/"
ARTICLE_ADDITIONAL_SOURCE_URL = "https://openai.com/index/hello-gpt-4o/"
ARTICLE = {
    "article_id": str(ARTICLE_ID),
    "title": "OpenAI announces GPT-4o and expands ChatGPT's free features",
    "content": (
        "On May 13, 2024, OpenAI announced GPT-4o, a new model intended to handle "
        "text, images, and voice more quickly than its earlier flagship model. The "
        "company said the release would also bring a wider set of ChatGPT tools to "
        "people using the free tier. The announcement described a staged rollout, "
        "with some capabilities available immediately and others planned for later."
        "\n\n"
        "OpenAI presented GPT-4o as a model that can work across several kinds of "
        "input. In its launch materials, the company said it was designed to accept "
        "combinations of text, audio, images, and video and to produce text, audio, "
        "or images. At the time of the announcement, however, the public rollout "
        "focused on text and image features. A more natural voice mode, including "
        "faster spoken responses and the ability to discuss live video, was planned "
        "for an initial release to some ChatGPT Plus users in the following weeks. "
        "OpenAI also highlighted improved image understanding and stronger support "
        "for languages beyond English."
        "\n\n"
        "The company began offering GPT-4o to ChatGPT Plus and Team users and said "
        "Enterprise availability would follow. Free users were also due to receive "
        "limited access. OpenAI said the free tier would gain tools that previously "
        "required a paid plan, including answers informed by web results, file "
        "uploads, data analysis and charts, conversations about photos, access to "
        "custom GPTs, and memory features. Free users would face limits on GPT-4o "
        "messages, while paid plans would have higher allowances. These details "
        "describe the launch in 2024, rather than current plan features or limits. "
        "OpenAI said it had more than 100 million weekly ChatGPT users at the time "
        "and planned to introduce the new free features over several weeks. The "
        "company gave image-based questions, such as translating a photographed "
        "menu and asking follow-up questions about it, as an example of what the "
        "new model could support. It also announced changes to ChatGPT's home "
        "screen and conversation layout."
        "\n\n"
        "The same announcement introduced a ChatGPT desktop app for macOS. OpenAI "
        "said Plus subscribers would receive it first, with wider access and a "
        "Windows version planned later. The app was designed to let people open "
        "ChatGPT with a keyboard shortcut, discuss screenshots, and use voice from "
        "their computer. For developers, OpenAI separately said GPT-4o was being "
        "made available through its API for text and image use. The broader audio "
        "and video capabilities were still being prepared for later release."
    ),
    "language": "en",
    "topic_id": TOPIC_ID,
}


@dataclass
class FakeContentManagement:
    assessment: dict[str, object] | None = None
    topic_summary: dict[str, object] | None = None
    missing_reads: int = 0

    def respond(self, request: httpx.Request) -> httpx.Response:
        assert "Authorization" not in request.headers
        path = request.url.path

        if request.method == "GET" and path == "/internal/v1/articles":
            if request.url.params.get("summary") == "missing":
                assert request.url.params.get("limit") == "25"
                self.missing_reads += 1
                return httpx.Response(
                    200, json={"items": [ARTICLE] if self.assessment is None else []}
                )

            assert request.url.params.get("topic_id") == TOPIC_ID
            assert request.url.params.get("limit") == "25"
            assert request.url.params.get("cursor") is None
            items = []
            if self.assessment is not None and self.assessment["text"] is not None:
                items.append(
                    {"article_id": str(ARTICLE_ID), "summary": self.assessment["text"]}
                )
            return httpx.Response(200, json={"items": items})

        if request.method == "GET" and path == "/internal/v1/topics":
            return httpx.Response(200, json=[{"id": TOPIC_ID}])

        if request.method == "PUT" and path == (
            f"/internal/v1/articles/{ARTICLE_ID}/summary"
        ):
            assert self.assessment is None
            self.assessment = json.loads(request.content)
            return httpx.Response(200, json={"article_id": str(ARTICLE_ID)})

        if request.method == "PUT" and path == (
            f"/internal/v1/topics/{TOPIC_ID}/summary"
        ):
            assert self.topic_summary is None
            self.topic_summary = json.loads(request.content)
            return httpx.Response(200)

        raise AssertionError(
            f"Unexpected Content Management request: {request.method} {path}"
        )


def run_one_article(ollama_url: str, model: str) -> FakeContentManagement:
    settings = WorkerSettings(
        _env_file=None,
        CONTENT_MANAGEMENT_BASE_URL="http://content-management",
        OLLAMA_BASE_URL=ollama_url,
        OLLAMA_MODEL=model,
    )
    fake = FakeContentManagement()
    with (
        closing(
            DownstreamClient(
                "content-management",
                settings.CONTENT_MANAGEMENT_BASE_URL,
                transport=httpx.MockTransport(fake.respond),
            )
        ) as content_client,
        httpx.Client(base_url=settings.OLLAMA_BASE_URL) as ollama_client,
    ):
        run_worker(settings, content_client, ollama_client, StaticTokenProvider())

    return fake


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ollama-url",
        default=DEFAULT_OLLAMA_URL,
        help="Host Ollama URL reachable from the VM (default: 10.0.2.2:11434)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Installed Ollama model (default: OLLAMA_MODEL from the service .env)",
    )
    args = parser.parse_args()

    fake = run_one_article(args.ollama_url, args.model)

    assert fake.missing_reads == 2
    assert fake.assessment is not None
    assert fake.topic_summary is not None
    assert fake.assessment["rejected"] is False, fake.assessment["quality_comment"]
    assert fake.topic_summary["text"] == fake.assessment["text"]
    print("Processed 1 article; Content Management was mocked.")
    print(f"Quality comment: {fake.assessment['quality_comment']}")
    print(f"Article summary: {fake.assessment['text']}")
    print(f"Topic summary: {fake.topic_summary['text']}")


if __name__ == "__main__":
    main()
