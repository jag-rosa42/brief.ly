from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict

from src.infrastructure.config.base import CLIENT_SECRETS_DIR, ServiceSettings


class ServiceTokenSettings(ServiceSettings):
    """
    What the worker needs to get a service token from Identity (ADR-0008).

    Separate from WorkerSettings because the client secret lives in another
    directory locally (see base.py). Like WorkerSettings, it is only built
    when the worker starts, so tests never need the secret.
    """

    # Only the secrets directory changes; the rest comes from ServiceSettings.
    model_config = SettingsConfigDict(secrets_dir=CLIENT_SECRETS_DIR)

    # Base URL of Identity, e.g. http://identity:8000
    IDENTITY_URL: str

    # This service's client secret at Identity, read from the file
    # ai_processing_client_secret (see base.py).
    AI_PROCESSING_CLIENT_SECRET: SecretStr
