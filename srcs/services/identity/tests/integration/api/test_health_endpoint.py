"""
Tests for the GET /health endpoint.

This integration test verifies that the health check:
- returns a 200 status code when the database is reachable
- reports both the application and database as healthy
"""

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response


@pytest.mark.integration
def test_health_check_reports_ok_when_database_is_reachable(client: TestClient):
    response: Response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
