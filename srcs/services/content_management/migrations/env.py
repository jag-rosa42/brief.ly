from alembic import context
from sqlalchemy import engine_from_config, pool

import src.infrastructure.database.models  # noqa: F401
from src.infrastructure.database.config import settings
from src.infrastructure.database.models.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# ---------------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------------
#
# There are two ways Alembic gets its database URL:
#
# 1. Pytest explicitly sets:
#
#       alembic_config.set_main_option(
#           "sqlalchemy.url",
#           database_url,
#       )
#
#    In that case, we MUST preserve that URL.
#
# 2. Normal CLI usage:
#
#       alembic upgrade head
#
#    In that case, alembic.ini has an empty sqlalchemy.url, so we fall back
#    to the application's Settings object.
#
# This allows the same env.py to work for both normal migrations and tests.
# ---------------------------------------------------------------------------

database_url: str | None = config.get_main_option("sqlalchemy.url")

if not database_url:
    config.set_main_option(
        "sqlalchemy.url",
        settings.SQLALCHEMY_DATABASE_URI,
    )


# ---------------------------------------------------------------------------
# SQLAlchemy metadata
# ---------------------------------------------------------------------------

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# ---------------------------------------------------------------------------
# Offline migrations
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations
# ---------------------------------------------------------------------------


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    """Run migrations using a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
