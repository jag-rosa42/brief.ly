from datetime import UTC, datetime

import pytest

from src.domain.entities import ArticleSummary


@pytest.fixture
def article_summary() -> ArticleSummary:
    return ArticleSummary(
        text="Article summary",
        summarized_at=datetime(2026, 11, 3, 10, tzinfo=UTC),
        llm_model="test-model",
        rejected=False,
        quality_comment="Passed quality review",
        generation_duration_ms=1250,
    )
