"""add persisted summaries

Revision ID: 8e8b4b9d67d1
Revises: c91e8f6a2d04
Create Date: 2026-11-03

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8e8b4b9d67d1"
down_revision: str | Sequence[str] | None = "c91e8f6a2d04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name in ("normalized_articles", "topics"):
        op.add_column(
            table_name,
            sa.Column("summary", sa.String(length=2000), nullable=True),
        )
        op.add_column(
            table_name,
            sa.Column(
                "summarized_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )
        op.add_column(
            table_name,
            sa.Column("summary_llm_model", sa.String(), nullable=True),
        )


def downgrade() -> None:
    for table_name in ("topics", "normalized_articles"):
        op.drop_column(table_name, "summary_llm_model")
        op.drop_column(table_name, "summarized_at")
        op.drop_column(table_name, "summary")
