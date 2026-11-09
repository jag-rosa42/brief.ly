from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict

from src.infrastructure.config.base import CLIENT_SECRETS_DIR, ServiceSettings


class ServiceTokenSettings(ServiceSettings):
    """
    What this service needs to get a service token from Identity (ADR-0008).

    Unlike app_settings, it is not built at import time: the dependency that
    creates the token provider builds it on first use, so tests that replace
    the catalogs never need the client secret.
    """

    # Only the secrets directory changes; the rest comes from ServiceSettings.
    model_config = SettingsConfigDict(secrets_dir=CLIENT_SECRETS_DIR)

    # Base URL of Identity, e.g. http://identity:8000
    IDENTITY_URL: str

    # This service's client secret at Identity, read from the file
    # personalization_client_secret (see base.py).
    PERSONALIZATION_CLIENT_SECRET: SecretStr
