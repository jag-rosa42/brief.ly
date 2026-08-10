"""
Tests for the SQLAlchemy Engine (src/infrastructure/database/config/engine.py).

The Engine object itself doesn't open a connection just by being created
(connections are opened lazily, on first use), so the first two tests are
still "unit" tests. The last one actually opens a connection to prove the
whole chain (Settings -> engine -> real Postgres) works.
"""
import pytest
from sqlalchemy import Engine, text
from sqlalchemy.pool import QueuePool

from src.infrastructure.database.config import engine, settings


def test_engine_is_configured_for_the_right_database():
    assert isinstance(engine, Engine)
    assert engine.url.drivername == (
        f"{settings.DATABASE_DIALECT}+{settings.DATABASE_DRIVER}"
    )
    assert engine.url.host == settings.POSTGRES_HOST
    assert engine.url.port == settings.POSTGRES_PORT
    assert engine.url.database == settings.POSTGRES_DB_NAME
    assert engine.url.username == settings.POSTGRES_USER


def test_engine_pool_settings():
    pool = engine.pool
    assert isinstance(pool, QueuePool)

@pytest.mark.integration
def test_engine_can_actually_connect_to_postgres():
    """
    This is the real proof that the app can talk to the database: open a
    connection through the configured engine and run a trivial query.
    """
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1
