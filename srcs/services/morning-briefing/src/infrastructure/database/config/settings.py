from typing import ClassVar, Literal

from pydantic import (
    PostgresDsn,
    SecretStr,
    computed_field,
)

from src.infrastructure.config.base import ServiceSettings


class DatabaseSettings(ServiceSettings):
    """
    Application configuration loaded from environment variables.

    BaseSettings automatically reads values from the environment and
    converts them to the declared Python types.
    """

    # -----------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------

    DATABASE_DIALECT: Literal["postgresql"] = "postgresql"

    # Driver used by the application.
    DATABASE_DRIVER: Literal["psycopg", "asyncpg"] = "psycopg"
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    # SecretStr prevents the password from being accidentally printed
    # or included in logs.
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB_NAME: str
    POSTGRES_TEST_DB_NAME: str | None = None
    POSTGRES_DEFAULT_DB_NAME: str

    # Synchronous SQLAlchemy / Alembic driver.
    _SYNC_DRIVER: ClassVar[str] = "psycopg"

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
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD.get_secret_value(),
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
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
            database=self.POSTGRES_DB_NAME, driver=self.DATABASE_DRIVER
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
        test_db_name = self.POSTGRES_TEST_DB_NAME or f"{self.POSTGRES_DB_NAME}_test"
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


database_settings = DatabaseSettings()
