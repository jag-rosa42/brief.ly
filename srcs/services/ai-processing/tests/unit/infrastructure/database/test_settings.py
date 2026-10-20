"""
Tests for DatabaseSettings (src/infrastructure/database/config/settings.py).

These tests verify that DatabaseSettings:
- loads database configuration from the environment
- builds the expected SQLAlchemy database URI
- protects the database password when represented as text
- uses explicitly provided values when creating a DatabaseSettings instance
- adds the `_test` suffix to the database name
- uses the synchronous PostgreSQL driver
"""

from sqlalchemy.engine import make_url

from src.infrastructure.config.app import app_settings
from src.infrastructure.database.config.settings import (
    DatabaseSettings,
    database_settings,
)


def test_settings_loads_values_from_environment():
    """The module-level database settings should have picked up .env."""
    assert app_settings.PROJECT_NAME
    assert database_settings.POSTGRES_HOST
    assert database_settings.POSTGRES_USER
    assert database_settings.POSTGRES_DB_NAME
    assert database_settings.POSTGRES_PORT == 5433


def test_database_uri_has_expected_shape():
    """
    SQLALCHEMY_DATABASE_URI is a @computed_field, i.e. it's rebuilt from the
    other fields every time it's accessed rather than stored directly.
    """
    uri = database_settings.SQLALCHEMY_DATABASE_URI

    assert uri.startswith("postgresql+psycopg://")
    assert database_settings.POSTGRES_USER in uri
    assert database_settings.POSTGRES_HOST in uri
    assert database_settings.POSTGRES_DB_NAME in uri
    assert str(database_settings.POSTGRES_PORT) in uri


def test_password_is_not_leaked_in_repr():
    """
    POSTGRES_PASSWORD is typed as SecretStr specifically so that printing
    or logging the settings object doesn't accidentally expose the raw
    password (e.g. in a stack trace or debug log).
    """
    real_password = database_settings.POSTGRES_PASSWORD.get_secret_value()

    assert real_password not in repr(database_settings.POSTGRES_PASSWORD)
    assert real_password not in repr(database_settings)


def test_database_uri_reflects_explicit_overrides():
    """
    Building a second DatabaseSettings instance with explicit kwargs
    (bypassing the .env file) confirms the URI is actually derived from the
    fields, rather than e.g. some other hardcoded default.
    """
    custom = DatabaseSettings(
        _env_file=None,
        POSTGRES_HOST="db.example.internal",
        POSTGRES_PORT=6543,
        POSTGRES_USER="tester",
        POSTGRES_PASSWORD="s3cret",
        POSTGRES_DB_NAME="test_db",
    )
    url = make_url(custom.SQLALCHEMY_DATABASE_URI)
    assert url.drivername == "postgresql+psycopg"
    assert url.username == "tester"
    assert url.password == "s3cret"
    assert url.host == "db.example.internal"
    assert url.port == 6543
    assert url.database == "test_db"


def test_database_name_is_suffixed_with_test():
    """
    Without an explicit override, TEST_DATABASE_URI should point to
    "<POSTGRES_DB_NAME>_test"
    """
    custom = DatabaseSettings(
        _env_file=None,
        POSTGRES_HOST="db.example.internal",
        POSTGRES_PORT=6543,
        POSTGRES_USER="tester",
        POSTGRES_PASSWORD="s3cret",
        POSTGRES_DB_NAME="my_app",
    )
    url = make_url(custom.TEST_DATABASE_URI)

    assert url.database == "my_app_test"


def test_database_uri_always_uses_sync_driver():
    custom = DatabaseSettings(
        _env_file=None,
        POSTGRES_HOST="db.example.internal",
        POSTGRES_PORT=6543,
        POSTGRES_USER="tester",
        POSTGRES_PASSWORD="s3cret",
        POSTGRES_DB_NAME="my_app",
        DATABASE_DRIVER="asyncpg",
    )
    url = make_url(custom.TEST_DATABASE_URI)
    assert url.drivername == "postgresql+psycopg"


def test_vector_extension_setting_is_parsed_as_boolean():
    custom = DatabaseSettings(
        _env_file=None,
        POSTGRES_HOST="localhost",
        POSTGRES_USER="tester",
        POSTGRES_PASSWORD="s3cret",
        POSTGRES_DB_NAME="test_db",
        POSTGRES_ENABLE_VECTOR_EXTENSION="true",
    )

    assert custom.POSTGRES_ENABLE_VECTOR_EXTENSION is True
