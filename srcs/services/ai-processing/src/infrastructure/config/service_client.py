from typing import Final

from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict

from src.infrastructure.config.base import CLIENT_SECRETS_DIR, ServiceSettings

# ---------------------------------------------------------------------------
# This service as an OAuth client of Identity (ADR-0008)
# ---------------------------------------------------------------------------
# Contract: docs/api/06_service-to-service.md. The client ID, audience and
# scopes must match this service's entry in Identity's registry
# (identity/src/infrastructure/oauth/service_clients.py). Constants, not
# settings: they never change between environments, so no .env can override
# them.
TOKEN_PATH: Final[str] = "/internal/v1/oauth/token"
CLIENT_ID: Final[str] = "ai-processing"
CONTENT_MANAGEMENT_AUDIENCE: Final[str] = "transcendence:content-management"
CONTENT_MANAGEMENT_SCOPES: Final[tuple[str, ...]] = (
    "topics:read",
    "articles:read",
    "summaries:write",
)
# The digest routes (ADR-0011) only read the topic summaries: their token
# asks for that scope only, so a bug in a route can never write a summary.
DIGEST_CONTENT_MANAGEMENT_SCOPES: Final[tuple[str, ...]] = ("topics:read",)


class ServiceClientSettings(ServiceSettings):
    """
    This service's credentials as an OAuth client of Identity: only what
    changes between environments (local, containers).

    Separate from WorkerSettings because the client secret lives in another
    directory locally (see base.py). Like WorkerSettings, it is only built
    when the worker starts, or on the first digest request (see
    api/dependencies.py), so tests never need the secret.
    """

    # Only the secrets directory changes; the rest comes from ServiceSettings.
    model_config = SettingsConfigDict(secrets_dir=CLIENT_SECRETS_DIR)

    # Base URL of Identity, e.g. http://identity:8000
    IDENTITY_URL: str

    # This service's client secret at Identity, read from the file
    # ai_processing_client_secret (see base.py).
    AI_PROCESSING_CLIENT_SECRET: SecretStr
