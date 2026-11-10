from datetime import UTC, datetime
from uuid import UUID

from src.application.port.unit_of_work import UnitOfWork
from src.domain.entities.api_key import ApiKey
from src.domain.repositories.api_key_repository import ApiKeyRepository


class RevokeApiKey:
    def __init__(
        self,
        uow: UnitOfWork,
        api_key_repository: ApiKeyRepository,
    ) -> None:
        self._uow: UnitOfWork = uow
        self._api_key_repository: ApiKeyRepository = api_key_repository

    def execute(self, account_id: UUID, api_key_id: UUID) -> None:
        """Revoke one of the account's keys. Immediate and idempotent.

        Immediate: verification reads the database on every request, with no
        cache, so the next public request with this key is refused.

        Idempotent, like logout: an unknown key, another account's key, or a
        key already revoked is not an error, there is just nothing to do.
        The caller gets the same answer in every case, so it can't learn
        whether a key ID belongs to someone else.
        """
        with self._uow:
            api_key: ApiKey | None = self._api_key_repository.find_by_id(api_key_id)

            if api_key is None or api_key.account_id != account_id:
                return

            if api_key.is_revoked():
                return

            api_key.revoke(datetime.now(UTC))

            # False only if the key was revoked concurrently: nothing left to do.
            if self._api_key_repository.update(api_key):
                self._uow.commit()
