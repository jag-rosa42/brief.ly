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
CLIENT_ID: Final[str] = "morning-briefing"
CONTENT_MANAGEMENT_AUDIENCE: Final[str] = "transcendence:content-management"
# One token for both catalogs: they run in the same process, so one token per
# catalog would not protect anything more.
CONTENT_MANAGEMENT_SCOPES: Final[tuple[str, ...]] = ("topics:read", "articles:read")


class ServiceClientSettings(ServiceSettings):
    """
    This service's credentials as an OAuth client of Identity: only what
    changes between environments (local, containers).

    Unlike app_settings, it is not built at import time: the dependency that
    creates the token provider builds it on first use, so tests that replace
    the catalogs never need the client secret.
    """

    # Only the secrets directory changes; the rest comes from ServiceSettings.
    model_config = SettingsConfigDict(secrets_dir=CLIENT_SECRETS_DIR)

    # Base URL of Identity, e.g. http://identity:8000
    IDENTITY_URL: str

    # This service's client secret at Identity, read from the file
    # morning_briefing_client_secret (see base.py).
    MORNING_BRIEFING_CLIENT_SECRET: SecretStr
