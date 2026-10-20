"""
Tests for the SQLAlchemy Engine (src/infrastructure/database/config/engine.py).

These tests verify that the engine:
- is configured with the expected database connection settings
- uses the expected connection pool
"""

from sqlalchemy import Engine
from sqlalchemy.pool import QueuePool

from src.infrastructure.database.config import database_settings, engine


def test_engine_is_configured_for_the_right_database():
    assert isinstance(engine, Engine)
    assert engine.url.drivername == (
        f"{database_settings.DATABASE_DIALECT}+{database_settings.DATABASE_DRIVER}"
    )
    assert engine.url.host == database_settings.POSTGRES_HOST
    assert engine.url.port == database_settings.POSTGRES_PORT
    assert engine.url.database == database_settings.POSTGRES_DB_NAME
    assert engine.url.username == database_settings.POSTGRES_USER


def test_engine_pool_settings():
    pool = engine.pool
    assert isinstance(pool, QueuePool)
