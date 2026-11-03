import uuid
from datetime import UTC, datetime

from sqlalchemy import ARRAY, UUID, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class NormalizedArticleModel(Base):
    __tablename__ = "normalized_articles"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "discovered_article_external_id",
            name=("uq_normalized_articles_source_discovered_article_external_id"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
    )

    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), nullable=False)
    discovered_article_external_id: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    publisher_name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    authors: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    image_url: Mapped[str | None] = mapped_column()
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    category: Mapped[str] = mapped_column()
    language: Mapped[str] = mapped_column()
    summary: Mapped[str | None] = mapped_column(String(2000))
    summarized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary_llm_model: Mapped[str | None] = mapped_column()
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
