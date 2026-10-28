"""use UTC ingestion timestamps

Revision ID: c91e8f6a2d04
Revises: 4c6a2f3b8d91
Create Date: 2026-10-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c91e8f6a2d04"
down_revision: str | Sequence[str] | None = "4c6a2f3b8d91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name, column_name in (
        ("sources", "last_successful_sync_at"),
        ("normalized_articles", "published_at"),
        ("normalized_articles", "fetched_at"),
    ):
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            postgresql_using=f"{column_name} AT TIME ZONE 'UTC'",
            existing_nullable=column_name != "fetched_at",
        )


def downgrade() -> None:
    for table_name, column_name in (
        ("sources", "last_successful_sync_at"),
        ("normalized_articles", "published_at"),
        ("normalized_articles", "fetched_at"),
    ):
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            postgresql_using=f"{column_name} AT TIME ZONE 'UTC'",
            existing_nullable=column_name != "fetched_at",
        )
