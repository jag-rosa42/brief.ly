"""
Shared pytest configuration and fixture registration for the test suite.

Fixture implementations are organized into dedicated modules under
``tests.fixtures``. This module serves as the composition root that makes
those fixtures available to the test suite through pytest's fixture
discovery mechanism.
"""

pytest_plugins: list[str] = [
    # Factory
    "tests.fixtures.factory",
    # Lowest-level fixtures first
    "tests.fixtures.security",
    # Sessions depend on security
    "tests.fixtures.sessions",

    # Accounts depend on sessions
    "tests.fixtures.accounts",

    # Infrastructure fixtures
    "tests.fixtures.database",
    "tests.fixtures.http",

]
