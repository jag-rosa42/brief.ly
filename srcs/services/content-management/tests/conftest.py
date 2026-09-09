"""
Shared pytest fixtures for integration tests.

These tests use a real PostgreSQL database configured through
settings.TEST_DATABASE_URI. The fixtures verify that the application's
database configuration, SQLAlchemy engine, sessions, migrations, and FastAPI
get_db dependency are correctly wired together.

The test database is created automatically if it does not exist.
Alembic migrations are applied once per pytest session.

Each test runs inside a transaction that is rolled back afterward, keeping
tests isolated while still exercising the real database and application
database stack.
"""

import logging
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, RootTransaction, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.compiler import IdentifierPreparer

from src.api.dependencies import get_db
from src.infrastructure.database.config import settings
from src.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

pytest_plugins = [
        "tests.fixtures.discovered_article",
        "tests.fixtures.discovered_article_model",
        "tests.fixtures.normalized_article",
        "tests.fixtures.normalized_article_model",
        "tests.fixtures.source",
        "tests.fixtures.source_model",
        "tests.fixtures.synchronization_time",
        ]


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
    # Connect to the defaut existing postgres db first
    # so we can check wether the test database exists
    # and create it if necessary
    existing_db_url: URL = target_url.set(database="postgres")
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
    Resolve the database url to test against.
    - If a valid database url is set, use it directly.
    - Otherwise, start a temporary PostgreSQL via Testcontainers.
      No setup required, and it's safe because the database exists only
      for this test session.
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
    One SQLAlchemy Engine for the entire pytest session
    """
    db_engine: Engine = create_engine(database_url, pool_pre_ping=True)

    with db_engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    yield db_engine
    db_engine.dispose()


# ---------------------------------------------------------------------------
# Alembic
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def migrate_database(database_url: str) -> None:
    """
    Run the migration once before the test suite
    """
    project_root: Path = Path(__file__).resolve().parents[1]
    alembic_config: Config = Config(file_=str(project_root / "alembic.ini"))
    alembic_config.set_main_option(
        name="sqlalchemy.url", value=database_url.replace("%", "%%")
    )
    command.upgrade(alembic_config, revision="head")


# ---------------------------------------------------------------------------
# Database transaction
# ---------------------------------------------------------------------------


# migrate_database is intentionally listed as a fixture dependency so
# Alembic migrations complete before the test transaction/connection is created.
@pytest.fixture
def db_connection(engine: Engine, migrate_database: None) -> Generator[Connection]:
    """
    One database connection and transaction per test.
    Everything is rollback after the test, so tests don't affect each other.
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
    A real SQLAlchemy Session, closed automatically after the test.
    The savepoint lets application code call session.commit() without committing
    the outer transaction, so everything can still be rolled back after the test.

    expire_on_commit=False keeps object attributes available after commit without
    requiring another database query.
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


# ---------------------------------------------------------------------------
# FastAPI Test Client
# ---------------------------------------------------------------------------


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    """
    TestClient configured to use the test database session.

    The application's get_db dependency is overridden so requests
    use the test database session instead of the production database.
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def concurrent_clients(engine: Engine) -> Generator[tuple[TestClient, TestClient]]:
    """
    Two TestClients using independent database sessions.

    Each request receives a new SQLAlchemy session backed by the shared
    test database engine, allowing concurrent requests to run in separate
    database transactions.
    """
    SessionLocal: sessionmaker[Session] = sessionmaker(
        bind=engine, expire_on_commit=False
    )

    def override_get_db() -> Generator[Session]:
        session: Session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client_a, TestClient(app) as client_b:
            yield client_a, client_b
    finally:
        app.dependency_overrides.pop(get_db, None)
