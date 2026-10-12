from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import ReturningUpdate, Update

from src.domain.entities.refresh_token import RefreshToken
from src.infrastructure.database.models.refresh_token import (
    RefreshToken as RefreshTokenModel,
)


class SqlAlchemyRefreshTokenRepository:
    def __init__(self, session: Session) -> None:
        self._session: Session = session

    def add(self, refresh_token: RefreshToken) -> None:
        refresh_token_model: RefreshTokenModel = self._to_model(refresh_token)
        self._session.add(refresh_token_model)

    def update(self, refresh_token: RefreshToken) -> bool:
        """Persist the revocation of a refresh token that is still active

        Compare-and-set Technique:
        The UPDATE only matches a row whose revoked_at is still NULL.
        A token can never be revoked twice, and an existing replaced_by_id can never
        be overwritten by a concurrent request, even if the caller
        did not lock the row first
        Returns:
            True if the stored token was updated
            False if it was already revoked (or does not exist).
        """
        statement: ReturningUpdate[tuple[UUID]] = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.id == refresh_token.id)
            .where(RefreshTokenModel.revoked_at.is_(None))
            .values(
                revoked_at=refresh_token.revoked_at,
                replaced_by_id=refresh_token.replaced_by,
            )
            .returning(RefreshTokenModel.id)
        )

        result: Result[tuple[UUID]] = self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    def find_by_id(self, refresh_token_id: UUID) -> RefreshToken | None:
        statement: Select[tuple[RefreshTokenModel]] = select(RefreshTokenModel).where(
            RefreshTokenModel.id == refresh_token_id
        )
        result: Result[tuple[RefreshTokenModel]] = self._session.execute(statement)
        refresh_token_model: RefreshTokenModel | None = result.scalar_one_or_none()
        if refresh_token_model is None:
            return None
        return self._to_domain(refresh_token_model)

    def find_by_id_for_update(self, refresh_token_id: UUID) -> RefreshToken | None:
        """Load a refresh token and bock its row until the transaction ends.

        Use SELECT ... FOR UPDATE:
        A concurrent transaction locking the same row blocks until this one commits
        or rolls back.
        populate_existing ensures the returned model contains the latest
        database values, even if it is already loaded in the session.

        Returns:
            The refresh token if found, otherwise None.
        """
        statement: Select[tuple[RefreshTokenModel]] = (
            select(RefreshTokenModel)
            .where(RefreshTokenModel.id == refresh_token_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        result: Result[tuple[RefreshTokenModel]] = self._session.execute(statement)
        refresh_token_model: RefreshTokenModel | None = result.scalar_one_or_none()
        if refresh_token_model is None:
            return None
        return self._to_domain(refresh_token_model)

    def revoke_all_for_account(self, account_id: UUID, now: datetime) -> None:
        statement: Update = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.account_id == account_id)
            .where(RefreshTokenModel.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        self._session.execute(statement)

    @staticmethod
    def _to_domain(model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            id=model.id,
            account_id=model.account_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            created_at=model.created_at,
            revoked_at=model.revoked_at,
            replaced_by=model.replaced_by_id,
        )

    @staticmethod
    def _to_model(refresh_token: RefreshToken) -> RefreshTokenModel:
        return RefreshTokenModel(
            id=refresh_token.id,
            account_id=refresh_token.account_id,
            token_hash=refresh_token.token_hash,
            expires_at=refresh_token.expires_at,
            created_at=refresh_token.created_at,
            revoked_at=refresh_token.revoked_at,
            replaced_by_id=refresh_token.replaced_by,
        )
