"""extract topic summaries

Revision ID: 65ac9d024e13
Revises: 3f14c2a8d901
Create Date: 2026-11-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "65ac9d024e13"
down_revision: str | Sequence[str] | None = "3f14c2a8d901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topic_summaries",
        sa.Column("topic_id", sa.String(), nullable=False),
        sa.Column("text", sa.String(length=2000), nullable=False),
        sa.Column("summarized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("llm_model", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("topic_id"),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO topic_summaries (topic_id, text, summarized_at, llm_model)
            SELECT id, summary, COALESCE(summarized_at, CURRENT_TIMESTAMP),
                   COALESCE(summary_llm_model, 'unknown')
            FROM topics
            WHERE summary IS NOT NULL
            """
        )
    )
    op.drop_column("topics", "summary_llm_model")
    op.drop_column("topics", "summarized_at")
    op.drop_column("topics", "summary")


def downgrade() -> None:
    op.add_column("topics", sa.Column("summary", sa.String(length=2000), nullable=True))
    op.add_column(
        "topics", sa.Column("summarized_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("topics", sa.Column("summary_llm_model", sa.String(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE topics AS topic
            SET summary = topic_summary.text,
                summarized_at = topic_summary.summarized_at,
                summary_llm_model = topic_summary.llm_model
            FROM topic_summaries AS topic_summary
            WHERE topic.id = topic_summary.topic_id
            """
        )
    )
    op.drop_table("topic_summaries")
