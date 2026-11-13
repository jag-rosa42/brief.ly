from pydantic import Field

from src.infrastructure.config.base import ServiceSettings


class WorkerSettings(ServiceSettings):
    CONTENT_MANAGEMENT_BASE_URL: str = Field(
        default="http://content-management:8000", min_length=1, max_length=2048
    )
    OLLAMA_BASE_URL: str = Field(min_length=1, max_length=2048)
    OLLAMA_MODEL: str = Field(min_length=1, max_length=256)
    OLLAMA_TIMEOUT_SECONDS: float = Field(default=120.0, gt=0)
    OLLAMA_CONTEXT_LENGTH: int = Field(default=8192, gt=0)
    ARTICLE_BATCH_SIZE: int = Field(default=25, ge=1, le=25)
