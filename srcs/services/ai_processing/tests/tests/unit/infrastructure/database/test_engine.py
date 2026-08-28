"""
Tests for the SQLAlchemy Engine (src/infrastructure/database/config/engine.py).

These tests verify that the engine:
- is configured with the expected database connection settings
- uses the expected connection pool
"""
from sqlalchemy import Engine
from sqlalchemy.pool import QueuePool

from src.infrastructure.database.config import engine, settings


def test_engine_is_configured_for_the_right_database():
    assert isinstance(engine, Engine)
    assert engine.url.drivername == (
        f"{settings.DATABASE_DIALECT}+{settings.DATABASE_DRIVER}"
    )
    assert engine.url.host == settings.AI_POSTGRES_HOST
    assert engine.url.port == settings.AI_POSTGRES_PORT
    assert engine.url.database == settings.AI_POSTGRES_DB_NAME
    assert engine.url.username == settings.AI_POSTGRES_USER


def test_engine_pool_settings():
    pool = engine.pool
    assert isinstance(pool, QueuePool)
