"""
Tests for SessionFactory (src/infrastructure/database/config/session.py).

These tests verify that SessionFactory:
- creates SQLAlchemy Session objects bound to the expected engine
- disables autoflush
"""

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
