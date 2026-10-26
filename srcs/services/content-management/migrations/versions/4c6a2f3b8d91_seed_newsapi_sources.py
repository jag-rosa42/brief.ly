"""seed NewsAPI sources

Revision ID: 4c6a2f3b8d91
Revises: df8dd7662ec0
Create Date: 2026-10-23

"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "4c6a2f3b8d91"
down_revision: str | Sequence[str] | None = "df8dd7662ec0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEWSAPI_CATEGORIES = (
    "business",
    "entertainment",
    "general",
    "health",
    "science",
    "sports",
    "technology",
)


def upgrade() -> None:
    sources_table = sa.table(
        "sources",
        sa.column("id", sa.UUID()),
        sa.column("category", sa.String()),
        sa.column("language", sa.String()),
        sa.column("interval_seconds", sa.Integer()),
        sa.column("enabled", sa.Boolean()),
        sa.column("last_successful_sync_at", sa.DateTime()),
    )
    op.bulk_insert(
        sources_table,
        [
            {
                "id": uuid4(),
                "category": category,
                "language": "en",
                "interval_seconds": 1_800,
                "enabled": True,
                "last_successful_sync_at": None,
            }
            for category in NEWSAPI_CATEGORIES
        ],
    )


def downgrade() -> None:
    sources_table = sa.table(
        "sources",
        sa.column("category", sa.String()),
        sa.column("language", sa.String()),
    )
    op.execute(
        sources_table.delete().where(
            sources_table.c.category.in_(NEWSAPI_CATEGORIES),
            sources_table.c.language == "en",
        )
    )
