"""
Tests for Settings (src/infrastructure/database/config/settings.py).

These tests verify that Settings:
- loads database configuration from the environment
- builds the expected SQLAlchemy database URI
- protects the database password when represented as text
- uses explicitly provided values when creating a Settings instance
- adds the `_test` suffix to the database name
- uses the synchronous PostgreSQL driver
"""

from sqlalchemy.engine import make_url

from src.infrastructure.database.config.settings import Settings, settings


def test_settings_loads_values_from_environment():
    """The module-level `settings` instance should have picked up .env."""
    assert settings.PROJECT_NAME
    assert settings.POSTGRES_HOST
    assert settings.POSTGRES_USER
    assert settings.POSTGRES_DB_NAME
    assert settings.POSTGRES_PORT == 5432


def test_database_uri_has_expected_shape():
    """
    SQLALCHEMY_DATABASE_URI is a @computed_field, i.e. it's rebuilt from the
    other fields every time it's accessed rather than stored directly.
    """
    uri = settings.SQLALCHEMY_DATABASE_URI

    assert uri.startswith("postgresql+psycopg://")
    assert settings.POSTGRES_USER in uri
    assert settings.POSTGRES_HOST in uri
    assert settings.POSTGRES_DB_NAME in uri
    assert str(settings.POSTGRES_PORT) in uri


def test_password_is_not_leaked_in_repr():
    """
    POSTGRES_PASSWORD is typed as SecretStr specifically so that printing
    or logging the settings object doesn't accidentally expose the raw
    password (e.g. in a stack trace or debug log).
    """
    real_password = settings.POSTGRES_PASSWORD.get_secret_value()

    assert real_password not in repr(settings.POSTGRES_PASSWORD)
    assert real_password not in repr(settings)


def test_database_uri_reflects_explicit_overrides():
    """
    Building a second Settings instance with explicit kwargs (bypassing the
    .env file) confirms the URI is actually derived from the fields, rather
    than e.g. some other hardcoded default.
    """
    custom = Settings(
        _env_file=None,
        PROJECT_NAME="test-project",
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
    custom = Settings(
        _env_file=None,
        PROJECT_NAME="test-project",
        POSTGRES_HOST="db.example.internal",
        POSTGRES_PORT=6543,
        POSTGRES_USER="tester",
        POSTGRES_PASSWORD="s3cret",
        POSTGRES_DB_NAME="my_app",
    )
    url = make_url(custom.TEST_DATABASE_URI)

    assert url.database == "my_app_test"


def test_database_uri_always_uses_sync_driver():
    custom = Settings(
        _env_file=None,
        PROJECT_NAME="test-project",
        POSTGRES_HOST="db.example.internal",
        POSTGRES_PORT=6543,
        POSTGRES_USER="tester",
        POSTGRES_PASSWORD="s3cret",
        POSTGRES_DB_NAME="my_app",
        DATABASE_DRIVER="asyncpg",
    )
    url = make_url(custom.TEST_DATABASE_URI)
    assert url.drivername == "postgresql+psycopg"
