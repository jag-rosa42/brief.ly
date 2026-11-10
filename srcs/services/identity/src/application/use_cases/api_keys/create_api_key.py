from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.application.port.api_key.generator import ApiKeyGenerator, GeneratedApiKey
from src.application.port.token_hasher import TokenHasher
from src.application.port.unit_of_work import UnitOfWork
from src.domain.entities.account import Account
from src.domain.entities.api_key import (
    API_KEY_LIFETIME,
    MAX_ACTIVE_API_KEYS_PER_ACCOUNT,
    ApiKey,
    ApiKeyScope,
)
from src.domain.exception import ApiKeyLimitReachedError, InvalidTokenError
from src.domain.repositories.account_repository import AccountRepository
from src.domain.repositories.api_key_repository import ApiKeyRepository


@dataclass(frozen=True)
class CreatedApiKey:
    api_key: ApiKey
    key: str  # the full key: returned once, here, and never stored


class CreateApiKey:
    def __init__(
        self,
        uow: UnitOfWork,
        account_repository: AccountRepository,
        api_key_repository: ApiKeyRepository,
        api_key_generator: ApiKeyGenerator,
        token_hasher: TokenHasher,
    ) -> None:
        self._uow: UnitOfWork = uow
        self._account_repository: AccountRepository = account_repository
        self._api_key_repository: ApiKeyRepository = api_key_repository
        self._api_key_generator: ApiKeyGenerator = api_key_generator
        self._token_hasher: TokenHasher = token_hasher

    def execute(
        self,
        account_id: UUID,
        name: str,
        scopes: frozenset[ApiKeyScope],
    ) -> CreatedApiKey:
        """Create an API key for an account.

        The key lives API_KEY_LIFETIME (48 h). Only its hash and prefix are
        stored; the full key is in the result, for the caller to show once.

        Raises:
            ApiKeyLimitReachedError: The account already has
                MAX_ACTIVE_API_KEYS_PER_ACCOUNT active keys.
            InvalidTokenError: The account no longer exists.
        """
        with self._uow:
            self._lock_account(account_id)

            now: datetime = datetime.now(UTC)
            self._check_active_key_limit(account_id, now)

            # Only the prefix and the hash are stored; the full key is returned once
            generated: GeneratedApiKey = self._api_key_generator.generate()
            api_key = ApiKey(
                id=uuid4(),
                account_id=account_id,
                name=name,
                prefix=generated.prefix,
                key_hash=self._token_hasher.hash(token=generated.key),
                scopes=scopes,
                created_at=now,
                expires_at=now + API_KEY_LIFETIME,
            )
            self._api_key_repository.add(api_key)

            self._uow.commit()

        return CreatedApiKey(api_key=api_key, key=generated.key)

    def _lock_account(self, account_id: UUID) -> None:
        # Locking the account row makes concurrent creations for the same
        # account wait for each other, so the count below can't go stale.
        account: Account | None = self._account_repository.find_by_id_for_update(
            account_id
        )
        if account is None:
            raise InvalidTokenError()

    def _check_active_key_limit(self, account_id: UUID, now: datetime) -> None:
        # Active = not revoked and not expired
        active_keys: int = self._api_key_repository.count_active_for_account(
            account_id, now
        )
        if active_keys >= MAX_ACTIVE_API_KEYS_PER_ACCOUNT:
            raise ApiKeyLimitReachedError()
