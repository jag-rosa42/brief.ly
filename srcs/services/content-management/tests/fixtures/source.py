from uuid import uuid4

import pytest

from src.domain.entities import Source


@pytest.fixture
def source() -> Source:
    return Source(
        id=uuid4(),
        category="science",
        language="fr",
        interval_seconds=300,
        enabled=True,
    )


@pytest.fixture
def source_b() -> Source:
    return Source(
        id=uuid4(),
        category="science",
        language="en",
        interval_seconds=300,
        enabled=True,
    )
