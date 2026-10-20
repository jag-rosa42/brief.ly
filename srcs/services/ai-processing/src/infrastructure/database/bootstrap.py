import psycopg
from psycopg import sql

from src.infrastructure.database.config.settings import database_settings


def _enable_pgvector_extension_if_configured(database_name: str) -> None:
    """Enable PostgreSQL's pgvector extension when configured."""
    if not database_settings.POSTGRES_ENABLE_VECTOR_EXTENSION:
        return

    with (
        psycopg.connect(
            host=database_settings.POSTGRES_HOST,
            port=database_settings.POSTGRES_PORT,
            user=database_settings.POSTGRES_USER,
            password=database_settings.POSTGRES_PASSWORD.get_secret_value(),
            dbname=database_name,
            autocommit=True,
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")


def ensure_database() -> None:
    """Create the service's database if it does not exist."""
    with (
        psycopg.connect(
            host=database_settings.POSTGRES_HOST,
            port=database_settings.POSTGRES_PORT,
            user=database_settings.POSTGRES_USER,
            password=database_settings.POSTGRES_PASSWORD.get_secret_value(),
            dbname=database_settings.POSTGRES_DEFAULT_DB_NAME,
            autocommit=True,
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (database_settings.POSTGRES_DB_NAME,),
        )

        if cursor.fetchone() is None:
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(database_settings.POSTGRES_DB_NAME)
                )
            )
            print(f"Created database: {database_settings.POSTGRES_DB_NAME}")
        else:
            print(f"Database already exists: {database_settings.POSTGRES_DB_NAME}")
    _enable_pgvector_extension_if_configured(database_settings.POSTGRES_DB_NAME)


if __name__ == "__main__":
    ensure_database()
