"""add topic summary generation duration

Revision ID: e2c4a62d17f0
Revises: b7f4e2c09a61
Create Date: 2026-11-09

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e2c4a62d17f0"
down_revision: str | Sequence[str] | None = "b7f4e2c09a61"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "topic_summaries",
        sa.Column("generation_duration_ms", sa.BigInteger(), nullable=True),
    )
    op.create_check_constraint(
        "ck_topic_summaries_generation_duration_ms_nonnegative",
        "topic_summaries",
        "generation_duration_ms >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_topic_summaries_generation_duration_ms_nonnegative",
        "topic_summaries",
        type_="check",
    )
    op.drop_column("topic_summaries", "generation_duration_ms")
