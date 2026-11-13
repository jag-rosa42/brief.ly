from pydantic import Field

from src.infrastructure.config.base import ServiceSettings


class DigestSettings(ServiceSettings):
    """
    What the digest routes need (ADR-0011).

    The Ollama and Content Management settings have the same names as the
    worker's (worker.py), so one .env serves both. Built on first use (see
    api/dependencies.py), not at import time: tests that replace the clients
    never need these values.
    """

    # Base URL of Personalization (the reader's profile), e.g.
    # http://personalization:8000
    PERSONALIZATION_URL: str = Field(min_length=1, max_length=2048)

    # Base URL of Content Management (topic summaries).
    CONTENT_MANAGEMENT_BASE_URL: str = Field(
        default="http://content-management:8000", min_length=1, max_length=2048
    )

    OLLAMA_BASE_URL: str = Field(min_length=1, max_length=2048)
    OLLAMA_MODEL: str = Field(min_length=1, max_length=256)
    # Longest wait for the next piece of an answer (and for the first one,
    # which includes loading the model and reading the prompt).
    OLLAMA_TIMEOUT_SECONDS: float = Field(default=120.0, gt=0)
