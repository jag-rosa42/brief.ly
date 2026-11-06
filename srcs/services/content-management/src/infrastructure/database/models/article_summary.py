import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class ArticleSummaryModel(Base):
    __tablename__ = "article_summaries"
    __table_args__ = (
        CheckConstraint(
            "generation_duration_ms >= 0",
            name="ck_article_summaries_generation_duration_ms_nonnegative",
        ),
    )

    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("normalized_articles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    text: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    summarized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    llm_model: Mapped[str] = mapped_column()
    rejected: Mapped[bool] = mapped_column(Boolean)
    quality_comment: Mapped[str] = mapped_column(Text)
    generation_duration_ms: Mapped[int] = mapped_column(BigInteger)
