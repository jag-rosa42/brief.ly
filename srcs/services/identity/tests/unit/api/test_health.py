# """
# Tests for the FastAPI app itself (src/main.py), using FastAPI's TestClient.

# TestClient wraps the app with an HTTP client (httpx under the hood) so we
# can send real requests without running a server process. Because get_db()
# isn't overridden here, /health genuinely round-trips through the real
# Postgres instance.
# """

"""
Tests for the FastAPI application (src/api/routers/system.py).

These tests verify that:
- the application uses the expected project name
- the root endpoint returns the expected response
- the health endpoint reports a database outage correctly
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from src.api.dependencies import get_db
from src.infrastructure.database.config import settings
from src.main import app


def test_app_title_matches_settings() -> None:
    assert app.title == settings.PROJECT_NAME


class _BrokenSession:
    """Represents a Session whose connection has been lost."""

    def execute(self, *args, **kwargs):
        raise ConnectionError("simulated database outage")


def _broken_get_db() -> Generator:
    """
    A fake version of get_db() that provides a session whose database
    operation always fails.

    The function must use `yield` because get_db() is a generator dependency.
    We want the session to be created successfully and the error to happen
    later, when the health endpoint tries to use the session.

    This simulates a database connection that is lost while handling
    the request, rather than a failure while FastAPI is creating
    the dependency.
    """
    yield _BrokenSession()


def test_health_check_reports_503_when_database_is_down() -> None:
    """
    We can't easily kill the real Postgres container mid-test, so this
    swaps out the get_db dependency for one that raises, purely to check
    that /health turns a database failure into a 503 instead of a 500.
    """
    app.dependency_overrides[get_db] = _broken_get_db
    try:
        with TestClient(app) as test_client:
            response: Response = test_client.get("health")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}


@pytest.fixture(autouse=True)
def _reset_dependency_overrides():
    yield
    app.dependency_overrides.clear()
