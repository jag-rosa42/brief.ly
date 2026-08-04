"""
Tests for the get_db dependency (src/api/dependencies.py).

get_db is a generator: it yields a Session, and only runs its cleanup
(`db.close()`) once the generator is driven to completion. FastAPI does
that driving for us on every request, but here we exercise it by hand to
prove the open/close lifecycle actually behaves as documented.
"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.dependencies import get_db


def test_get_db_yields_a_working_session():
    generator = get_db()
    session = next(generator)

    try:
        assert isinstance(session, Session)
        assert session.execute(text("SELECT 1")).scalar() == 1
    finally:
        # Drive the generator to completion so its `finally: db.close()`
        # runs, the same way FastAPI does after a request finishes.
        generator.close()


def test_get_db_closes_the_session_once_exhausted():
    generator = get_db()
    session = next(generator)
    session.close = MagicMock(wraps=session.close)

    # Exhausting the generator (StopIteration) runs the `finally` block.
    next(generator, None)

    session.close.assert_called_once()


def test_get_db_closes_session_even_if_the_caller_raises():
    generator = get_db()
    session = next(generator)
    session.close = MagicMock(wraps=session.close)

    # Simulate a route handler raising mid-request: FastAPI throws the
    # exception into the generator, which should still run its `finally`.
    with pytest.raises(RuntimeError):
        generator.throw(RuntimeError("boom"))

    session.close.assert_called_once()
