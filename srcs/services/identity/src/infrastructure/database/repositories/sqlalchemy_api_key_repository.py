from datetime import datetime
from uuid import UUID

from sqlalchemy import ColumnElement, Select, func, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import ReturningUpdate

from src.domain.entities.api_key import ApiKey, ApiKeyScope
from src.infrastructure.database.models.api_key import ApiKey as ApiKeyModel
from src.infrastructure.database.repositories.query import one_or_none


def _is_active(now: datetime) -> ColumnElement[bool]:
    """SQL version of ApiKey.is_active(): not revoked and not expired at `now`."""
    return ApiKeyModel.revoked_at.is_(None) & (ApiKeyModel.expires_at > now)


class SqlAlchemyApiKeyRepository:
    def __init__(self, session: Session) -> None:
        self._session: Session = session

    def add(self, api_key: ApiKey) -> None:
        self._session.add(self._to_model(api_key))

    def update(self, api_key: ApiKey) -> bool:
        """Persist the revocation of a key that is still active.

        Compare-and-set, like the refresh tokens: the UPDATE only matches a
        row whose revoked_at is still NULL, so a key is never revoked twice.

        Returns:
            True if the stored key was updated
            False if it was already revoked (or does not exist).
        """
        statement: ReturningUpdate[tuple[UUID]] = (
            update(ApiKeyModel)
            .where(ApiKeyModel.id == api_key.id)
            .where(ApiKeyModel.revoked_at.is_(None))
            .values(revoked_at=api_key.revoked_at)
            .returning(ApiKeyModel.id)
        )
        result: Result[tuple[UUID]] = self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    def find_by_id(self, api_key_id: UUID) -> ApiKey | None:
        statement: Select[tuple[ApiKeyModel]] = select(ApiKeyModel).where(
            ApiKeyModel.id == api_key_id
        )
        return one_or_none(self._session, statement, self._to_domain)

    def find_by_hash(self, key_hash: str) -> ApiKey | None:
        # Uses the index of the uq_api_keys_key_hash constraint.
        statement: Select[tuple[ApiKeyModel]] = select(ApiKeyModel).where(
            ApiKeyModel.key_hash == key_hash
        )
        return one_or_none(self._session, statement, self._to_domain)

    def count_active_for_account(self, account_id: UUID, now: datetime) -> int:
        statement: Select[tuple[int]] = (
            select(func.count())
            .select_from(ApiKeyModel)
            .where(ApiKeyModel.account_id == account_id)
            .where(_is_active(now))
        )
        return self._session.execute(statement).scalar_one()

    def list_active_for_account(self, account_id: UUID, now: datetime) -> list[ApiKey]:
        statement: Select[tuple[ApiKeyModel]] = (
            select(ApiKeyModel)
            .where(ApiKeyModel.account_id == account_id)
            .where(_is_active(now))
            .order_by(ApiKeyModel.created_at.desc())
        )
        models = self._session.execute(statement).scalars().all()
        return [self._to_domain(model) for model in models]

    # def _first_or_none(self, statement: Select[tuple[ApiKeyModel]]) -> ApiKey | None:
    #     result: Result[tuple[ApiKeyModel]] = self._session.execute(statement)
    #     api_key_model: ApiKeyModel | None = result.scalar_one_or_none()
    #     if api_key_model is None:
    #         return None
    #     return self._to_domain(api_key_model)

    @staticmethod
    def _to_domain(model: ApiKeyModel) -> ApiKey:
        return ApiKey(
            id=model.id,
            account_id=model.account_id,
            name=model.name,
            prefix=model.prefix,
            key_hash=model.key_hash,
            # The database holds plain strings; the domain holds the enum.
            scopes=frozenset(ApiKeyScope(scope) for scope in model.scopes),
            created_at=model.created_at,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
        )

    @staticmethod
    def _to_model(api_key: ApiKey) -> ApiKeyModel:
        return ApiKeyModel(
            id=api_key.id,
            account_id=api_key.account_id,
            name=api_key.name,
            prefix=api_key.prefix,
            key_hash=api_key.key_hash,
            # Sorted, so the same scopes are always stored in the same order.
            scopes=sorted(scope.value for scope in api_key.scopes),
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            revoked_at=api_key.revoked_at,
        )
