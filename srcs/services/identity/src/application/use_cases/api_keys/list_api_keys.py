from datetime import UTC, datetime
from uuid import UUID

from src.domain.entities.api_key import ApiKey
from src.domain.repositories.api_key_repository import ApiKeyRepository


class ListApiKeys:
    def __init__(self, api_key_repository: ApiKeyRepository) -> None:
        self._api_key_repository: ApiKeyRepository = api_key_repository

    def execute(self, account_id: UUID) -> list[ApiKey]:
        """The account's active keys (not revoked, not expired), newest first.

        Revoked and expired keys are left out: they can't be used anymore,
        so the user has nothing to do with them.
        """
        return self._api_key_repository.list_active_for_account(
            account_id, datetime.now(UTC)
        )
