from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import Update

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

    def update(self, refresh_token: RefreshToken) -> None:
        refresh_token_model = self._session.get(
            RefreshTokenModel,
            refresh_token.id,
        )

        if refresh_token_model is None:
            raise ValueError(f"Refresh token {refresh_token.id} not found")

        refresh_token_model.revoked_at = refresh_token.revoked_at
        refresh_token_model.replaced_by_id = refresh_token.replaced_by

    def find_by_id(self, refresh_token_id: UUID) -> RefreshToken | None:
        statement: Select[tuple[RefreshTokenModel]] = select(RefreshTokenModel).where(
            RefreshTokenModel.id == refresh_token_id
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

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise

    def rollback(self) -> None:
        self._session.rollback()

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
