"""
Tests for the FastAPI app itself (src/main.py), using FastAPI's TestClient.

TestClient wraps the app with an HTTP client (httpx under the hood) so we
can send real requests without running a server process. Because get_db()
isn't overridden here, /health genuinely round-trips through the real
Postgres instance.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_db
from src.infrastructure.database.config import settings
from src.main import app


def test_app_title_matches_settings():
    assert app.title == settings.PROJECT_NAME


def test_root_endpoint(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

@pytest.mark.integration
def test_health_check_reports_ok_when_database_is_reachable(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


class _BrokenSession:
    """Stands in for a Session whose connection has dropped."""

    def execute(self, *args, **kwargs):
        raise ConnectionError("simulated database outage")


def _broken_get_db() -> Generator:
    """
    A stand-in for get_db() that yields a session which fails on use.

    It must still yield (rather than raise directly) so the failure
    happens inside health_check's own try/except, same as a real query
    failing against a database that's gone away mid-request - not during
    FastAPI's dependency resolution, which the route can't catch.
    """
    yield _BrokenSession()


def test_health_check_reports_503_when_database_is_down(client: TestClient):
    """
    We can't easily kill the real Postgres container mid-test, so this
    swaps out the get_db dependency for one that raises, purely to check
    that /health turns a database failure into a 503 instead of a 500.
    """
    app.dependency_overrides[get_db] = _broken_get_db
    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}

@pytest.fixture(autouse=True)
def _reset_dependency_overrides():
    yield
    app.dependency_overrides.clear()
