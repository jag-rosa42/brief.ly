from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class TopicModel(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(
        primary_key=True,
    )
    summary: Mapped[str | None] = mapped_column(String(2000))
    summarized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary_llm_model: Mapped[str | None] = mapped_column()
