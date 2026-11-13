"""
Shared pytest configuration and fixture registration for the test suite.

Fixture implementations are organized into dedicated modules under
``tests.fixtures``. This module serves as the composition root that makes
those fixtures available to the test suite through pytest's fixture
discovery mechanism.
"""

pytest_plugins: list[str] = [
    "tests.fixtures.auth",
    "tests.fixtures.database",
    "tests.fixtures.http",
]
