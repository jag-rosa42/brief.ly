from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.domain.entities.profile import Profile
from src.infrastructure.database.models.profile import Profile as ProfileModel
from src.infrastructure.database.models.profile_interest import (
    ProfileInterest as ProfileInterestModel,
)


class SqlAlchemyProfileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, account_id: UUID) -> Profile | None:
        name = self._session.execute(
            select(ProfileModel.name).where(ProfileModel.account_id == account_id)
        ).scalar_one_or_none()
        if name is None:
            return None
        topic_ids = (
            self._session.execute(
                select(ProfileInterestModel.topic_id).where(
                    ProfileInterestModel.account_id == account_id
                )
            )
            .scalars()
            .all()
        )
        return Profile(
            account_id=account_id,
            name=name,
            topic_ids=frozenset(topic_ids),
        )

    def _insert_profile(self, profile: Profile) -> bool:
        created_account_id = self._session.execute(
            insert(ProfileModel)
            .values(account_id=profile.account_id, name=profile.name)
            .on_conflict_do_nothing(index_elements=[ProfileModel.account_id])
            .returning(ProfileModel.account_id)
        ).scalar_one_or_none()
        return created_account_id is not None

    def _update_profile(self, profile: Profile) -> None:
        self._session.execute(
            update(ProfileModel)
            .where(ProfileModel.account_id == profile.account_id)
            .values(name=profile.name, updated_at=func.now())
        )

    def _insert_interests(self, profile: Profile) -> None:
        self._session.execute(
            insert(ProfileInterestModel),
            [
                {"account_id": profile.account_id, "topic_id": topic_id}
                for topic_id in profile.topic_ids
            ],
        )

    def _replace_interests(self, profile: Profile) -> None:
        self._session.execute(
            delete(ProfileInterestModel).where(
                ProfileInterestModel.account_id == profile.account_id
            )
        )
        self._insert_interests(profile)

    def upsert(self, profile: Profile) -> bool:
        if self._insert_profile(profile):
            self._insert_interests(profile)
            return True

        self._update_profile(profile)
        self._replace_interests(profile)
        return False
