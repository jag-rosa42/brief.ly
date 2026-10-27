"""
Row lock taken by SqlAlchemyProfileRepository.find_by_id_for_update.

These tests open several independent connections on the test database, so
they cannot use the per-test rollback of ``db_session``: the profile is really
committed and deleted at the end.
"""

from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, delete, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from src.domain.entities.profile import Profile
from src.infrastructure.database.models.profile import Profile as ProfileModel
from src.infrastructure.database.repositories.sqlalchemy_profile_repository import (
    SqlAlchemyProfileRepository,
)


@pytest.fixture
def committed_account_id(engine: Engine) -> Generator[UUID]:
    account_id: UUID = uuid4()
    with Session(engine) as session:
        SqlAlchemyProfileRepository(session).upsert(
            Profile.create(account_id, name="John", topic_ids=["science"])
        )
        session.commit()
    try:
        yield account_id
    finally:
        # ON DELETE CASCADE removes the profile's interests too.
        with Session(engine) as session:
            session.execute(
                delete(ProfileModel).where(ProfileModel.account_id == account_id)
            )
            session.commit()


def test_find_by_id_for_update_blocks_a_second_locker_but_not_a_plain_read(
    engine: Engine,
    committed_account_id: UUID,
) -> None:
    with Session(engine) as holder, Session(engine) as waiter:
        # The holder takes the lock and keeps its transaction open.
        SqlAlchemyProfileRepository(holder).find_by_id_for_update(committed_account_id)

        # A plain SELECT is not blocked (PostgreSQL MVCC).
        assert SqlAlchemyProfileRepository(waiter).find_by_id(committed_account_id)

        # A second FOR UPDATE must wait. Give up after 200 ms instead of
        # hanging, and check that it actually had to wait.
        waiter.execute(text("SET LOCAL lock_timeout = '200ms'"))
        with pytest.raises(OperationalError):
            SqlAlchemyProfileRepository(waiter).find_by_id_for_update(
                committed_account_id
            )
        waiter.rollback()

        # Ending the holder's transaction releases the lock.
        holder.rollback()
        assert SqlAlchemyProfileRepository(waiter).find_by_id_for_update(
            committed_account_id
        )
        waiter.rollback()
