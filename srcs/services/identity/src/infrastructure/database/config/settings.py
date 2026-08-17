from pathlib import Path
from typing import Literal

from pydantic import (
    PostgresDsn,
    SecretStr,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[4]
_container_secrets = Path("/run/secrets")

if _container_secrets.exists():
    SECRETS_DIR = _container_secrets
else:
    ROOT_DIR = Path(__file__).resolve().parents[7]
    SECRETS_DIR = ROOT_DIR / "shared" / "secrets"

#TODO: debug prints to remove later
print(f"SECRET_DIR={SECRETS_DIR}")

class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    BaseSettings automatically reads values from the environment and
    converts them to the declared Python types.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        secrets_dir=SECRETS_DIR,
    )
    DATABASE_DIALECT: Literal["postgresql"] = "postgresql"
    DATABASE_DRIVER: Literal["psycopg", "asyncpg"] = "psycopg"
    PROJECT_NAME: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    # SecretStr prevents the password from being accidentally printed
    # or included in logs.
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB_NAME: str

    # Origins allowed to call this API from a browser (CORS).
    BACKEND_CORS_ORIGINS: list[str] = []

    @computed_field(repr=False)
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Build the SQLAlchemy database URL from the individual settings.

        SQLAlchemy uses this URL to determine:

        - which database to connect to
        - which DBAPI driver to use
        - how to authenticate
        - which database to open

        Example:

        postgresql+psycopg://user:password@localhost:5432/my_database
        """
        return str(
            PostgresDsn.build(
                scheme=f"{self.DATABASE_DIALECT}+{self.DATABASE_DRIVER}",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD.get_secret_value(),
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB_NAME,
            )
        )

    @computed_field(repr=False)
    @property
    def alembic_database_uri(self) -> str:
        return self.SQLALCHEMY_DATABASE_URI.replace("+asyncpg", "+psycopg")


settings = Settings()

#TODO: debug prints to remove later
print("DB HOST:", settings.POSTGRES_HOST)
print("DB PORT:", settings.POSTGRES_PORT)
print("DB USER:", settings.POSTGRES_USER)
print("DB NAME:", settings.POSTGRES_DB_NAME)
print("DB URI:", settings.SQLALCHEMY_DATABASE_URI.replace(
    settings.POSTGRES_PASSWORD.get_secret_value(), "***"
))
