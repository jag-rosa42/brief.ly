from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class TopicModel(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(
            primary_key=True,
            )
