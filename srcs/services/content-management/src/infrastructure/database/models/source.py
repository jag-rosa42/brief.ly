import uuid
from datetime import datetime

from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class SourceModel(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
    )

    category: Mapped[str] = mapped_column()
    language: Mapped[str] = mapped_column()
    interval_seconds: Mapped[int] = mapped_column()
    enabled: Mapped[bool] = mapped_column()
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(
            nullable=True
            )
