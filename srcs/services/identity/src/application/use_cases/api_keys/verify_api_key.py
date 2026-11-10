from datetime import UTC, datetime

from src.application.port.api_key.token_creator import PublicApiTokenCreator
from src.application.port.token_hasher import TokenHasher
from src.domain.entities.api_key import ApiKey
from src.domain.exception import InvalidApiKeyError
from src.domain.repositories.api_key_repository import ApiKeyRepository

# ----- Phantom token exchange (ADR-0009) -----
#
#   program ── X-API-Key: tr_... ──▶ gateway ── ForwardAuth ──▶ Identity
#                                                                  │
#                                             hash the key, find it by hash
#                                                                  │
#                                                    ┌─────────────┴────────────┐
#                                                    │                          │
#                                       missing, unknown,                    active
#                                       revoked or expired                      │
#                                                    │                          ▼
#                                                    ▼              sign a 60 s public API
#                                       401 INVALID_API_KEY         token (sub = owner,
#                                       (gateway returns it)        scope = key's scopes)
#                                                                               │
#                                                                               ▼
#                                                     200 + Authorization: Bearer <token>
#                                                     the gateway puts it in the request
#                                                     it forwards to the service


class VerifyApiKey:
    """Exchange an API key for a public API token (the phantom token pattern).

    Read-only on purpose (ADR-0009): no "last used" date is written, so the
    gateway's check never writes to the database. There is no cache either,
    so a revoked key is refused on the very next request.
    """

    def __init__(
        self,
        api_key_repository: ApiKeyRepository,
        token_hasher: TokenHasher,
        public_api_token_creator: PublicApiTokenCreator,
    ) -> None:
        self._api_key_repository: ApiKeyRepository = api_key_repository
        self._token_hasher: TokenHasher = token_hasher
        self._public_api_token_creator: PublicApiTokenCreator = public_api_token_creator

    def execute(self, key: str | None) -> str:
        """Return a public API token for the key's owner, with the key's scopes.

        Raises:
            InvalidApiKeyError: The key is missing, unknown, revoked or expired.
        """
        if not key:
            raise InvalidApiKeyError()

        # Keys are stored only as hashes: hash what we received, the same way
        # CreateApiKey did, and look it up.
        api_key: ApiKey | None = self._api_key_repository.find_by_hash(
            self._token_hasher.hash(key)
        )

        if api_key is None or not api_key.is_active(datetime.now(UTC)):
            raise InvalidApiKeyError()

        return self._public_api_token_creator.create_public_api_token(
            account_id=api_key.account_id,
            scopes=api_key.scopes,
        )
