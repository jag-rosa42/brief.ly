from dataclasses import dataclass
from typing import Self
from uuid import UUID

from src.domain.exception import InvalidInterestsError, InvalidNameError

NAME_MIN_LENGTH = 1
NAME_MAX_LENGTH = 50
MAX_TOPICS = 4
MIN_TOPICS = 1


@dataclass
class Profile:
    account_id: UUID
    name: str
    topic_ids: frozenset[str]

    @classmethod
    def create(cls, account_id: UUID, name: str, topic_ids: list[str]) -> Self:
        return cls(
            account_id=account_id,
            name=cls._validate_name(name),
            topic_ids=cls._validate_topics(topic_ids),
        )

    def rename(self, new_name: str) -> None:
        self.name = self._validate_name(new_name)

    def replace_interests(self, new_topic_ids: list[str]) -> None:
        self.topic_ids = self._validate_topics(new_topic_ids)

    @staticmethod
    def _validate_name(name: str) -> str:
        trimmed_name = name.strip()
        if not NAME_MIN_LENGTH <= len(trimmed_name) <= NAME_MAX_LENGTH:
            raise InvalidNameError()
        return trimmed_name

    @staticmethod
    def _validate_topics(topic_ids: list[str]) -> frozenset[str]:
        topics = frozenset(topic_ids)

        if len(topics) != len(topic_ids):
            raise InvalidInterestsError()

        if not MIN_TOPICS <= len(topics) <= MAX_TOPICS:
            raise InvalidInterestsError()

        return topics
