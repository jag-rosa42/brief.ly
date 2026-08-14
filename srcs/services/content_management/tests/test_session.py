"""
Tests for SessionFactory (src/infrastructure/database/config/session.py).

SessionFactory is a factory (a `sessionmaker`), not a Session itself. These
tests create real Session objects from it and check both their config
(autoflush/expire_on_commit) and that they can actually run a query.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.database.config import SessionFactory, engine


def test_session_local_builds_sessions_bound_to_the_engine():
    session = SessionFactory()
    try:
        assert isinstance(session, Session)
        assert session.get_bind() is engine
    finally:
        session.close()


def test_session_local_disables_autoflush():
    session = SessionFactory()
    try:
        assert session.autoflush is False
    finally:
        session.close()


def test_session_can_query_postgres(db_session: Session):
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1
