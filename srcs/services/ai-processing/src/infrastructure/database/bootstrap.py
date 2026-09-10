import psycopg
from psycopg import sql

from src.infrastructure.database.config.settings import settings


def _enable_pgvector_extension_if_configured(database_name: str) -> None:
    """active PostgresSQL's pgvector extension"""
    if not settings.POSTGRES_ENABLE_VECTOR_EXTENSION:
        return

    with (
        psycopg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            dbname=database_name,
            autocommit=True,
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            "CREATE EXTENSION IF NOT EXISTS Vector"
        )

def ensure_database() -> None:
    """Create the service's database if it does not exist."""
    with (
        psycopg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            dbname="postgres",
            autocommit=True,
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (settings.POSTGRES_DB_NAME,),
        )

        if cursor.fetchone() is None:
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(settings.POSTGRES_DB_NAME)
                )
            )
            print(f"Created database: {settings.POSTGRES_DB_NAME}")
        else:
            print(f"Database already exists: {settings.POSTGRES_DB_NAME}")
    _enable_pgvector_extension_if_configured(settings.POSTGRES_DB_NAME)


if __name__ == "__main__":
    ensure_database()
