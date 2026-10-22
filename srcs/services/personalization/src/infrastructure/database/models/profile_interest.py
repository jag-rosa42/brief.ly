import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class ProfileInterest(Base):
    __tablename__ = "profile_interest"

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profile.account_id", ondelete="CASCADE"),
        primary_key=True,
    )

    topic_id: Mapped[str] = mapped_column(
        String(),
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
