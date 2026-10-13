from pydantic import SecretStr

from src.infrastructure.config.base import ServiceSettings


class SecuritySettings(ServiceSettings):
    """
    Token and session configuration.

    Kept separate from the database Settings on purpose: only the running
    service needs the JWT keys.
    The migration container imports the database settings only, so it never receives
    (and never needs) the private key.

    The keys are read from the secrets directory (/run/secrets in a container,
    shared/secrets locally): the file `jwt_private_key` fills JWT_PRIVATE_KEY
    because pydantic-settings matches names case-insensitively.
    """

    # -----------------------------------------------------------------------
    # Keys
    # -----------------------------------------------------------------------
    JWT_PRIVATE_KEY: SecretStr
    JWT_PUBLIC_KEY: str

    # -----------------------------------------------------------------------
    # Lifetimes
    # -----------------------------------------------------------------------

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

security_settings = SecuritySettings()