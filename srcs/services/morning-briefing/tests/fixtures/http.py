"""
HTTP fixtures for FastAPI integration tests.

This module provides TestClient fixtures configured to interact with the
FastAPI application using the test database.

The database fixtures are intentionally kept separate from these fixtures:
``database.py`` is responsible for database lifecycle and transaction
isolation, while this module is responsible for wiring the FastAPI
application to those database resources.

The regular ``client`` fixture uses the isolated per-test ``db_session``.
The ``concurrent_clients`` fixture intentionally creates independent
sessions so tests can exercise multiple independent database transactions.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from shared_auth.testing import FakeTokenIssuer
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.dependencies import get_db
from src.main import app
from tests.fixtures.auth import SERVICE_AUDIENCE

# ---------------------------------------------------------------------------
# FastAPI Test Client
# ---------------------------------------------------------------------------


@pytest.fixture
def client(db_session: Session, token_issuer: FakeTokenIssuer) -> Generator[TestClient]:
    """
    Provide a FastAPI TestClient configured to use the test's database session.

    The application's ``get_db`` dependency is overridden so API requests
    use the same SQLAlchemy Session managed by the test transaction.
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # The app verifies the issuer's test tokens instead of Identity's.
    token_issuer.override_authenticator(
        app, service_audience=SERVICE_AUDIENCE, public_api=True
    )

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def concurrent_clients(
    engine: Engine, token_issuer: FakeTokenIssuer
) -> Generator[tuple[TestClient, TestClient]]:
    """
    Provide Two FastAPI TestClients using independent database sessions.

    Each request receives a new SQLAlchemy session backed by the shared
    test database engine, allowing concurrent requests to run in separate
    database transactions.

    Unlike ``client``, these clients do not share the per-test transaction.
    Each request receives a session from its own sessionmaker, allowing tests
    to exercise behavior involving independent database transactions,
    concurrent requests, locking, race conditions, and similar scenarios.

    Changes made through these clients are not automatically covered by the
    normal per-test transaction rollback fixture, so tests using this fixture
    should explicitly clean up any persistent state they create when needed.
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
    token_issuer.override_authenticator(
        app, service_audience=SERVICE_AUDIENCE, public_api=True
    )

    try:
        with TestClient(app) as client_a, TestClient(app) as client_b:
            yield client_a, client_b
    finally:
        app.dependency_overrides.clear()
