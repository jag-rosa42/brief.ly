from sqlalchemy import create_engine

from src.infrastructure.database.config.settings import database_settings

"""
The Engine is SQLAlchemy's interface to the database.

It is responsible for:

- Opening database connections.
- Managing the connection pool.
- Executing SQL statements.
- Beginning and ending database transactions.

The Engine is created once when the application starts and is shared
by every SQLAlchemy Session.
"""
# Connection pool configuration.
#
# SQLAlchemy keeps a pool of reusable database connections instead of
# opening a brand new connection for every request.
#
# These settings control the size and behavior of that pool.
engine = create_engine(
    url=database_settings.SQLALCHEMY_DATABASE_URI,
    pool_size=5,  # Keep up to 5 idle/open connections ready.
    max_overflow=10,  # Allow up to 10 extra temporary connections during spikes.
    pool_timeout=30,  # Wait up to 30 seconds for a free connection.
    pool_recycle=3600,  # Recreate connections every hour to avoid stale connections.
    pool_pre_ping=True,  # Verify a connection is still alive before using it.
)
