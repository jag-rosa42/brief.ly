"""
Database fixtures for integration tests.

This module provides the complete database environment required by
integration tests:

- Resolving and validating the test database URL.
- Creating the PostgreSQL test database when necessary.
- Creating and disposing the SQLAlchemy engine.
- Applying Alembic migrations once per pytest session.
- Creating an isolated database transaction for each test.
- Providing a SQLAlchemy Session bound to that transaction.

The normal test flow is:

    database_url
        ↓
      engine
        ↓
  db_connection
        ↓
    db_session

The per-test transaction is rolled back after each test so that tests
can use the real PostgreSQL database and the real SQLAlchemy stack
without leaving persistent data behind.

Some tests, such as concurrency tests, may intentionally use the
session-independent ``engine`` fixture directly when they need multiple
independent database transactions.
"""

import logging
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, Engine, RootTransaction, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session
from sqlalchemy.sql.compiler import IdentifierPreparer

from src.infrastructure.database.config import settings

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Test Database
# ---------------------------------------------------------------------------


def _assert_test_database(url: str) -> None:
    """
    Prevent accidentally running tests against a non-test database.
    """
    database_name: str | None = make_url(url).database

    if not database_name:
        raise RuntimeError(f"Database URL has no database name: {url!r}")

    if "test" not in database_name.lower():
        raise RuntimeError(
            f"Refusing to run tests against database "
            f"{database_name!r} - expected a test database URL"
        )


def _create_test_database_if_needed(url: str) -> None:
    """
    Create the PostgreSQL test database if it does not already exist.

    PostgreSQL does not allow CREATE DATABASE inside a transaction, so
    we connect to the existing database with AUTOCOMMIT enabled.
    """
    target_url: URL = make_url(url)
    database_name: str | None = target_url.database
    if not database_name:
        raise RuntimeError(f"Test database URL has no database name: {url!r}")

    # We can not connect to the test database if it does not exist.
    # Connect to an existing database first so we check wether the test database exists
    # and create it if necessary
    existing_db_url: URL = target_url.set(database=settings.POSTGRES_DEFAULT_DB_NAME)
    engine: Engine = create_engine(existing_db_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM pg_database
                    WHERE datname = :database_name
                    """
                ),
                {"database_name": database_name},
            ).scalar()

            if not exists:
                preparer: IdentifierPreparer = connection.dialect.identifier_preparer
                quoted_database_name: str = preparer.quote(database_name)
                connection.execute(text(f"CREATE DATABASE {quoted_database_name}"))
                logger.info(
                    "Test database %r did not exist; created it successfully.",
                    database_name,
                )
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")  # Set up once and reused by all tests in the session
def database_url() -> str:
    """
    Resolve and validate the PostgreSQL database used by integration tests.

    The configured test database is created automatically when it does not
    already exist.
    """

    url: str = settings.TEST_DATABASE_URI
    _assert_test_database(url)
    _create_test_database_if_needed(url)
    return url


# ---------------------------------------------------------------------------
# SQLAlchemy Engine
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def engine(database_url: str) -> Generator[Engine]:
    """
    Provide one SQLAlchemy Engine shared by the entire test session.

    The engine is connectivity-checked before being yielded and disposed
    after the test session completes.
    """
    db_engine: Engine = create_engine(database_url, pool_pre_ping=True)

    with db_engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    yield db_engine
    db_engine.dispose()


# ---------------------------------------------------------------------------
# Alembic
# ---------------------------------------------------------------------------


def _find_project_root() -> Path:
    """Find the project root by locating the Alembic configuration file.

    Starting from this module's directory, walk up the directory tree until
    an ``alembic.ini`` file is found.

    Returns:
        The path to the project root containing ``alembic.ini``.

    Raises:
        RuntimeError: If ``alembic.ini`` cannot be found in any parent
            directory.
    """
    root_marker: str = "alembic.ini"
    for parent in Path(__file__).resolve().parents:
        if (parent / root_marker).is_file():
            return parent
    raise RuntimeError("Could not find alembic.ini")


@pytest.fixture(scope="session", autouse=True)
def migrate_database(database_url: str) -> None:
    """
    Apply all Alembic migrations before integration tests run.

    Migrations are executed once per pytest session and are intentionally
    independent of the per-test transaction used for test isolation.
    """
    project_root: Path = _find_project_root()
    alembic_config: Config = Config(file_=str(project_root / "alembic.ini"))
    alembic_config.set_main_option(
        name="sqlalchemy.url", value=database_url.replace("%", "%%")
    )
    command.upgrade(alembic_config, revision="head")


# ---------------------------------------------------------------------------
# Database transaction
# ---------------------------------------------------------------------------


@pytest.fixture
def db_connection(engine: Engine, migrate_database: None) -> Generator[Connection]:
    """
    Provide a database connection with one transaction per test.

    The transaction is rolled back when the test finishes, ensuring that
    database changes made during the test do not persist into subsequent
    tests.

    ``migrate_database`` is an explicit dependency so migrations are
    guaranteed to complete before the test transaction is created.
    """
    connection: Connection = engine.connect()
    transaction: RootTransaction = connection.begin()

    try:
        yield connection
    finally:
        transaction.rollback()
        connection.close()


# ---------------------------------------------------------------------------
# SQLAlchemy Session
# ---------------------------------------------------------------------------


@pytest.fixture
def db_session(db_connection: Connection) -> Generator[Session]:
    """
    Provide a SQLAlchemy Session bound to the test transaction.

    ``create_savepoint`` allows application code to call ``session.commit()``
    without committing the outer transaction owned by ``db_connection``.
    Consequently, all changes can still be rolled back when the test ends.

    ``expire_on_commit=False`` keeps ORM object attributes available after
    commits without requiring an additional database query.
    """
    session: Session = Session(
        bind=db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
