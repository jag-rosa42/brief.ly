import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    __table_args__ = (
        # Two keys never share a hash (the key is 256 random bits), and the
        # unique constraint gives the index the gateway's lookup needs.
        UniqueConstraint(
            "key_hash",
            name="uq_api_keys_key_hash",
        ),
        # The database refuses scopes other than read and write, and an empty
        # list, even if a bug or a hand-written SQL query tries to store them.
        # `<@` means "is contained in". Duplicates are refused earlier, by the
        # request schema. A new scope needs a migration that changes this list.
        CheckConstraint(
            "cardinality(scopes) > 0 AND scopes <@ ARRAY['read', 'write']::text[]",
            name="ck_api_keys_scopes",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # DB-level cascade: PostgreSQL deletes an account's API keys with it.
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    prefix: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    key_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # A PostgreSQL array, e.g. {read,write}: the API and the token both speak
    # in lists of scopes. The values are checked before they get here
    # (ApiKeyScope, request schema), and again by ck_api_keys_scopes above.
    scopes: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
