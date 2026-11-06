"""allow null text for rejected article summaries

Revision ID: b7f4e2c09a61
Revises: 65ac9d024e13
Create Date: 2026-11-06

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7f4e2c09a61"
down_revision: str | Sequence[str] | None = "65ac9d024e13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "article_summaries", "text", existing_type=sa.String(2000), nullable=True
    )
    op.execute("UPDATE article_summaries SET text = NULL WHERE rejected = TRUE")


def downgrade() -> None:
    op.execute("UPDATE article_summaries SET text = '' WHERE text IS NULL")
    op.alter_column(
        "article_summaries", "text", existing_type=sa.String(2000), nullable=False
    )
