"""
Tests for the get_db dependency (src/api/dependencies.py).

get_db is a generator: it yields a Session, and only runs its cleanup
(`db.close()`) once the generator is driven to completion. FastAPI does
that driving for us on every request, but here we exercise it by hand to
prove the open/close lifecycle actually behaves as documented.

These tests verify that get_db:
- provides a working database Session
- closes the Session when the generator finishes
- closes the Session even when an exception occurs
"""

from collections.abc import Generator

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.orm import Session

from src.api import dependencies
from src.api.dependencies import get_db


@pytest.fixture
def bind_get_db_to_test_connection(
    monkeypatch: pytest.MonkeyPatch, db_connection: Connection
) -> None:
    """
    Make get_db use the test database connection instead of the real database.

    get_db uses dependencies.SessionFactory, so we replace that reference with a factory
    that creates a Session bound to the test connection.

    The monkeypatch is automatically undone after each test.
    """

    def test_session_factory() -> Session:
        return Session(bind=db_connection, join_transaction_mode="create_savepoint")

    monkeypatch.setattr(dependencies, "SessionFactory", test_session_factory)


def test_get_db_yields_a_working_session(bind_get_db_to_test_connection) -> None:
    """
    Verify that get_db creates and yiels a usable SQLAlchemy Session
    """

    generator: Generator[Session] = get_db()
    # `get_db()` is a generator because it uses `yield` instead of `return`.
    # A generator pauses when it reaches `yield` and can be resumed later.
    #
    # `next()` is a built-in Python function used to resume a generator
    # and get its next yielded value. Here, it starts `get_db()` and runs
    # until `yield db`, so `session` receives the Session yielded by `get_db()`.
    session = next(generator)

    try:
        # Verify that get_db yielded a real SQLAlchemy Session.
        assert isinstance(session, Session)

        # Verify that the Session is actually usable by executing SQL.
        assert session.execute(text("SELECT 1")).scalar() == 1
    finally:
        # The generator is currently paused at `yield db`.
        #
        # Closing the generator makes Python run the `finally` block
        # inside get_db(), which calls `db.close()`.
        #
        # FastAPI normally handles this cleanup automatically.
        # We do it manually here because we are testing get_db directly.
        generator.close()


def test_get_db_closes_the_session_once_exhausted(
    bind_get_db_to_test_connection,
    monkeypatch,  # a pytest fixture that pytest automatically provides
):
    """
    Verify that get_db closes the Session even when the caller raises.
    """
    generator: Generator[Session] = get_db()
    session: Session = next(generator)

    # Keep track of calls to session.close().
    close_calls: list[int] = []

    # Replace close() with a function that records the call.
    monkeypatch.setattr(
        session,
        "close",
        lambda: close_calls.append(1),
    )

    # Exhausting the generator (StopIteration) runs the `finally` block.
    next(generator, None)

    assert close_calls == [1]


def test_get_db_closes_session_even_if_the_caller_raises(
    bind_get_db_to_test_connection,
    monkeypatch,
):
    generator: Generator[Session] = get_db()
    session: Session = next(generator)

    # Keep track of calls to session.close().
    close_calls = []

    # Replace close() with a function that records the call.
    monkeypatch.setattr(
        session,
        "close",
        lambda: close_calls.append(1),
    )

    # Simulate a route handler raising mid-request: FastAPI throws the
    # exception into the generator, which should still run its `finally` block.
    with pytest.raises(RuntimeError):
        generator.throw(RuntimeError("route handler failed"))

    assert close_calls == [1]
