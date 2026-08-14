"""
Shared pytest fixtures.

These tests connect to a real PostgreSQL instance (the one described by
src/.env) rather than swapping in SQLite or mocks. The goal of this suite
is specifically to prove that Settings -> engine -> SessionFactory -> get_db
are wired together correctly against a real database.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.infrastructure.database.config import SessionFactory
from src.main import app


@pytest.fixture
def db_session() -> Generator[Session]:
    """A real SQLAlchemy Session, closed automatically after the test."""
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient]:
    """A FastAPI TestClient around the real app (real DB, no overrides)."""
    with TestClient(app) as test_client:
        yield test_client
