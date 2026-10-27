from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from src.domain.entities.profile import (
    MAX_TOPICS,
    MIN_TOPICS,
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    Profile,
)


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


class UpsertProfileRequest(BaseModel):
    """Body of PUT /me/profile: every field is optional, at least one is required."""

    # Refuse unknown fields: a typo like "names" must be reported,
    # not silently dropped (which would then look like an empty body).
    model_config = ConfigDict(extra="forbid")

    name: (
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True,
                min_length=NAME_MIN_LENGTH,
                max_length=NAME_MAX_LENGTH,
            ),
        ]
        | None
    ) = None
    topic_ids: (
        Annotated[list[str], Field(min_length=MIN_TOPICS, max_length=MAX_TOPICS)] | None
    ) = None

    @field_validator("topic_ids")
    @classmethod
    def topic_ids_have_no_duplicates(
        cls, topic_ids: list[str] | None
    ) -> list[str] | None:
        if topic_ids is not None and len(set(topic_ids)) != len(topic_ids):
            raise ValueError("topic_ids must not contain duplicates")
        return topic_ids

    @model_validator(mode="after")
    def has_at_least_one_field(self) -> Self:
        if self.name is None and self.topic_ids is None:
            raise ValueError("at least one of name or topic_ids is required")
        return self
