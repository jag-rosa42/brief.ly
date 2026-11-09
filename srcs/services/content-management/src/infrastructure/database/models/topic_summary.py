from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class TopicSummaryModel(Base):
    __tablename__ = "topic_summaries"
    __table_args__ = (
        CheckConstraint(
            "generation_duration_ms >= 0",
            name="ck_topic_summaries_generation_duration_ms_nonnegative",
        ),
    )

    topic_id: Mapped[str] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"),
        primary_key=True,
    )
    text: Mapped[str] = mapped_column(String(2000))
    summarized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    llm_model: Mapped[str] = mapped_column()
    generation_duration_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
