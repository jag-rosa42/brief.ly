from datetime import datetime
from typing import Self

from pydantic import BaseModel

from src.domain.entities.profile import Profile


class ProfileResponse(BaseModel):
    name: str
    topic_ids: list[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, profile: Profile) -> Self:
        """Build the response from a profile loaded from the database.

        `topic_ids` are sorted alphabetically, so the response does not depend
        on the order in which the topics were stored."""

        if profile.created_at is None or profile.updated_at is None:
            raise ValueError("The profile must be loaded from the database")
        return cls(
            name=profile.name,
            topic_ids=sorted(profile.topic_ids),
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
