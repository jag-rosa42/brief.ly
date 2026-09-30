import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    DateTime,
    ForeignKey,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.models.base import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.account import Account


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # DB-level cascade: PostgreSQL deletes refresh_tokens when their account is deleted.
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # DB-level FK: ensures this references an existing refresh token in the rotation chain
    # NULL if this token has not been replaced.
    # This is a self-referencing foreign key
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("refresh_tokens.id"),
        nullable=True,
    )

    account: Mapped[Account] = relationship(
        "Account",
        back_populates="refresh_tokens",
    )

    # SQLAlchemy relationship: provides access to the RefreshTokenModel
    # that replaced this token. The foreign key is stored in replaced_by_id.
    replaced_by_token: Mapped[RefreshToken | None] = relationship(
        "RefreshToken",
        foreign_keys=[replaced_by_id],
        remote_side="RefreshToken.id",
    )
