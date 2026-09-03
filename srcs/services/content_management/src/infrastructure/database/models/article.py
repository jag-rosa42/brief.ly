import uuid
from datetime import UTC, datetime

from sqlalchemy import ARRAY, UUID, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class ArticleModel(Base):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "external_id",
            name="uq_articles_source_external_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4,
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey("sources.id"))
    external_id: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    editor: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column()
    content: Mapped[str] = mapped_column()
    authors: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    image_url: Mapped[str | None] = mapped_column()
    published_at: Mapped[datetime | None] = mapped_column()
    category: Mapped[str] = mapped_column()
    language: Mapped[str] = mapped_column()
    fetched_at: Mapped[datetime] = mapped_column(
            default=lambda: datetime.now(UTC)
            )
