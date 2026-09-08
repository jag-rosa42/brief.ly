from pathlib import Path
from typing import ClassVar, Literal

from pydantic import (
    PostgresDsn,
    SecretStr,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[4]


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
    )

    # -----------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------

    DATABASE_DIALECT: Literal["postgresql"] = "postgresql"

    # Driver used by the application.
    DATABASE_DRIVER: Literal["psycopg", "asyncpg"] = "psycopg"
    PROJECT_NAME: str
    AI_POSTGRES_HOST: str
    AI_POSTGRES_PORT: int = 5432
    AI_POSTGRES_USER: str
    # SecretStr prevents the password from being accidentally printed
    # or included in logs.
    AI_POSTGRES_PASSWORD: SecretStr
    AI_POSTGRES_DB_NAME: str
    AI_POSTGRES_TEST_DB_NAME: str | None = None

    # Synchronous SQLAlchemy / Alembic driver.
    _SYNC_DRIVER: ClassVar[str] = "psycopg"

    # -----------------------------------------------------------------------
    # CORS
    # -----------------------------------------------------------------------

    # Origins allowed to call this API from a browser (CORS).
    BACKEND_CORS_ORIGINS: list[str] = []

    # -----------------------------------------------------------------------
    # Database URL builder
    # -----------------------------------------------------------------------

    def _build_database_uri(self, *, database: str, driver: str) -> str:
        """
        Build a PostgreSQL SQLAlchemy DSN.
        Every *_DATABASE_URI / *_uri property below assembles its URL through this
        one method, so host/port credentials logic is defined exactly once

        Example:

            postgresql+psycopg://user:password@localhost:5432/database
        """
        return str(
            PostgresDsn.build(
                scheme=f"{self.DATABASE_DIALECT}+{driver}",
                username=self.AI_POSTGRES_USER,
                password=self.AI_POSTGRES_PASSWORD.get_secret_value(),
                host=self.AI_POSTGRES_HOST,
                port=self.AI_POSTGRES_PORT,
                path=database,
            )
        )

    # -----------------------------------------------------------------------
    # Application database
    # -----------------------------------------------------------------------

    @computed_field(repr=False)
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Database URL used by the application.

        SQLAlchemy uses this URL to determine:
        - which database to connect to
        - which DBAPI driver to use
        - how to authenticate
        - which database to open

        Example:

        postgresql+psycopg://user:password@localhost:5432/my_database
        """
        return self._build_database_uri(
            database=self.AI_POSTGRES_DB_NAME, driver=self.DATABASE_DRIVER
        )

    # -----------------------------------------------------------------------
    # Test database
    # -----------------------------------------------------------------------

    @computed_field(repr=False)
    @property
    def TEST_DATABASE_URI(self) -> str:
        """
        Database URL used by pytest.

        If POSTGRES_TEST_DB_NAME is not configured, the test database
        defaults to:

            <POSTGRES_DB_NAME>_test

        Example:

            identity_db_test
        """
        test_db_name = self.AI_POSTGRES_TEST_DB_NAME or f"{self.AI_POSTGRES_DB_NAME}_test"
        return self._build_database_uri(database=test_db_name, driver=self._SYNC_DRIVER)

    # -----------------------------------------------------------------------
    # Alembic
    # -----------------------------------------------------------------------

    @computed_field(repr=False)
    @property
    def alembic_database_uri(self) -> str:
        """
        URL specifically suitable for Alembic.

        Alembic runs synchronously, so it must use psycopg rather than
        asyncpg.
        """
        return self.SQLALCHEMY_DATABASE_URI.replace("+asyncpg", "+psycopg")


settings = Settings()
print(f"url={settings.SQLALCHEMY_DATABASE_URI}")