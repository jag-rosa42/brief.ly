from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Profile:
    """The user's profile, as Personalization returns it."""

    name: str
    topic_ids: tuple[str, ...]
    saved_article_ids: tuple[UUID, ...]
