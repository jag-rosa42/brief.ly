"""
Shared pytest configuration and fixture registration for the test suite.

Fixture implementations are organized into dedicated modules under
``tests.fixtures`` (same layout as Identity's tests). This module serves as
the composition root that makes those fixtures available to the test suite
through pytest's fixture discovery mechanism.

The tests use made-up names ("example:...", "caller-service", "/resources"):
the package must work for any service, so its tests depend on none of them.
"""

pytest_plugins: list[str] = [
    # Lowest-level fixtures first: the issuer's key pair and the token factory
    "tests.fixtures.security",
    # Settings, verifier and authenticator depend on the public key
    "tests.fixtures.authentication",
    # Fake token endpoint, fake clock and mock transports for the HTTP clients
    "tests.fixtures.clients",
    # FastAPI test app, depends on the settings
    "tests.fixtures.http",
]
