from uuid import uuid4

import pytest

from src.infrastructure.database.models import (
    SourceModel,
)


@pytest.fixture
def source_model() -> SourceModel:
    return SourceModel(
        id=uuid4(),
        category="science",
        language="fr",
        interval_seconds=300,
        enabled=True,
    )
