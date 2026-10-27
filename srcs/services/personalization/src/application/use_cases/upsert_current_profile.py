from uuid import UUID

from src.application.port.topic_catalog import TopicCatalog
from src.application.port.unit_of_work import UnitOfWork
from src.domain.entities.profile import Profile
from src.domain.exception import ProfileFieldsRequiredError, UnknownTopicsError
from src.domain.repositories.profile_repository import ProfileRepository


class UpsertCurrentProfile:
    def __init__(
        self,
        uow: UnitOfWork,
        profile_repository: ProfileRepository,
        topic_catalog: TopicCatalog,
    ) -> None:
        self._uow: UnitOfWork = uow
        self._profiles: ProfileRepository = profile_repository
        self._topic_catalog: TopicCatalog = topic_catalog

    def execute(
        self,
        account_id: UUID,
        name: str | None,
        topic_ids: list[str] | None,
    ) -> tuple[Profile, bool]:
        if topic_ids is not None:
            self._ensure_topics_exist(topic_ids)

        with self._uow:
            profile: Profile | None = self._profiles.find_by_id_for_update(account_id)
            if profile is None:
                if name is None or topic_ids is None:
                    missing_fields = [
                        field
                        for field, value in (("name", name), ("topic_ids", topic_ids))
                        if value is None
                    ]
                    raise ProfileFieldsRequiredError(missing_fields)

                profile = Profile.create(account_id, name, topic_ids)
            else:
                if name is not None:
                    profile.rename(name)
                if topic_ids is not None:
                    profile.replace_interests(topic_ids)

            created: bool = self._profiles.upsert(profile)
            saved: Profile | None = self._profiles.find_by_id(account_id)
            self._uow.commit()

        if saved is None:
            raise RuntimeError("The profile was just saved but cannot be read back")
        return saved, created

    def _ensure_topics_exist(self, topic_ids: list[str]) -> None:
        unknown_topic_ids: set[str] = (
            set(topic_ids) - self._topic_catalog.get_all().keys()
        )
        if unknown_topic_ids:
            raise UnknownTopicsError(unknown_topic_ids)
