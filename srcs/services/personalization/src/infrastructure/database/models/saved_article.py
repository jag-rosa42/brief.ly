import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class SavedArticle(Base):
    __tablename__ = "saved_article"

    # DB-level cascade: PostgreSQL deletes the saved articles when their profile
    # is deleted.
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profile.account_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Plain id of an article owned by Content Management.
    # No foreign key: the articles table lives in another service's database.
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    # Snapshot of the article, copied from Content Management at save time.
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    topic_id: Mapped[str] = mapped_column(String(), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    read_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
