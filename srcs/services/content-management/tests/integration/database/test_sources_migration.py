import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.database.models import SourceModel

EXPECTED_CATEGORIES = {
    "business",
    "entertainment",
    "general",
    "health",
    "science",
    "sports",
    "technology",
}


@pytest.mark.integration
def test_migration_seeds_the_newsapi_sources(db_session: Session):
    sources = db_session.scalars(select(SourceModel)).all()

    assert len(sources) == len(EXPECTED_CATEGORIES)
    assert {source.category for source in sources} == EXPECTED_CATEGORIES
    assert len({source.id for source in sources}) == len(sources)
    assert all(source.id.version == 4 for source in sources)
    assert all(source.language == "en" for source in sources)
    assert all(source.interval_seconds == 1_800 for source in sources)
    assert all(source.enabled for source in sources)
    assert all(source.last_successful_sync_at is None for source in sources)
