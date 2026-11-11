"""
Shared pytest configuration and fixture registration for the test suite.

Fixture implementations are organized into dedicated modules under
``tests.fixtures``. This module serves as the composition root that makes
those fixtures available to the test suite through pytest's fixture
discovery mechanism.
"""

pytest_plugins: list[str] = [
    "tests.fixtures.auth",
    # Domain fixtures
    "tests.fixtures.article_summary",
    "tests.fixtures.discovered_article",
    "tests.fixtures.normalized_article",
    "tests.fixtures.normalized_article_model",
    "tests.fixtures.source",
    "tests.fixtures.source_model",
    "tests.fixtures.synchronization_time",
    "tests.fixtures.ingestion_lock",
    "tests.fixtures.unit_of_work",
    # Infrastructure fixtures
    "tests.fixtures.database",
    "tests.fixtures.http",
]
