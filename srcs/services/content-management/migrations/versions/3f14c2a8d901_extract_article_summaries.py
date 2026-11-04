"""extract article summaries

Revision ID: 3f14c2a8d901
Revises: 8e8b4b9d67d1
Create Date: 2026-11-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3f14c2a8d901"
down_revision: str | Sequence[str] | None = "8e8b4b9d67d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "article_summaries",
        sa.Column("article_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.String(length=2000), nullable=False),
        sa.Column("summarized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("llm_model", sa.String(), nullable=False),
        sa.Column("rejected", sa.Boolean(), nullable=False),
        sa.Column("quality_comment", sa.Text(), nullable=False),
        sa.Column("generation_duration_ms", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "generation_duration_ms >= 0",
            name="ck_article_summaries_generation_duration_ms_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["normalized_articles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("article_id"),
    )

    # The added quality fields did not exist on legacy summaries. Neutral values
    # preserve those rows without pretending that they went through quality review.
    op.execute(
        sa.text(
            """
            INSERT INTO article_summaries (
                article_id,
                text,
                summarized_at,
                llm_model,
                rejected,
                quality_comment,
                generation_duration_ms
            )
            SELECT
                id,
                summary,
                COALESCE(summarized_at, fetched_at),
                COALESCE(summary_llm_model, 'unknown'),
                FALSE,
                '',
                0
            FROM normalized_articles
            WHERE summary IS NOT NULL
            """
        )
    )

    op.drop_column("normalized_articles", "summary_llm_model")
    op.drop_column("normalized_articles", "summarized_at")
    op.drop_column("normalized_articles", "summary")


def downgrade() -> None:
    op.add_column(
        "normalized_articles",
        sa.Column("summary", sa.String(length=2000), nullable=True),
    )
    op.add_column(
        "normalized_articles",
        sa.Column("summarized_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "normalized_articles",
        sa.Column("summary_llm_model", sa.String(), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE normalized_articles AS article
            SET
                summary = article_summary.text,
                summarized_at = article_summary.summarized_at,
                summary_llm_model = article_summary.llm_model
            FROM article_summaries AS article_summary
            WHERE article.id = article_summary.article_id
            """
        )
    )

    op.drop_table("article_summaries")
