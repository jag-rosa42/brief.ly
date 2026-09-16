from datetime import UTC, datetime

import pytest


@pytest.fixture
def synchronization_time() -> datetime:
    return datetime(2026, 8, 14, 8, 30, tzinfo=UTC)
