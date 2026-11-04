from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.models.base import Base
from src.infrastructure.database.models.topic_summary import TopicSummaryModel


class TopicModel(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(
        primary_key=True,
    )
    summary: Mapped[TopicSummaryModel | None] = relationship(
        cascade="all, delete-orphan",
        lazy="joined",
        single_parent=True,
        uselist=False,
    )
