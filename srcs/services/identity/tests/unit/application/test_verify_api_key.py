from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.application.use_cases.api_keys.verify_api_key import VerifyApiKey
from src.domain.entities.api_key import API_KEY_LIFETIME, ApiKeyScope
from src.domain.exception import InvalidApiKeyError
from tests.fixtures.api_keys import FakeApiKeyRepository, FakePublicApiTokenCreator
from tests.fixtures.factory import build_api_key
from tests.fixtures.security import FakeTokenHasher

KEY: str = "tr_the-key-the-program-sends"
READ_WRITE = frozenset({ApiKeyScope.READ, ApiKeyScope.WRITE})


class TestVerifyApiKey:
    def test_returns_a_token_for_the_owner_with_the_key_scopes(
        self,
        verify_api_key: VerifyApiKey,
        api_key_repository: FakeApiKeyRepository,
        token_hasher: FakeTokenHasher,
        public_api_token_creator: FakePublicApiTokenCreator,
    ) -> None:
        api_key = build_api_key(key_hash=token_hasher.hash(KEY), scopes=READ_WRITE)
        api_key_repository.add(api_key)

        token: str = verify_api_key.execute(KEY)

        assert token == f"fake-public-api-token-for-{api_key.account_id}"
        assert public_api_token_creator.calls == [(api_key.account_id, READ_WRITE)]

    @pytest.mark.parametrize("key", [None, ""])
    def test_refuses_a_missing_key(
        self, verify_api_key: VerifyApiKey, key: str | None
    ) -> None:
        with pytest.raises(InvalidApiKeyError):
            verify_api_key.execute(key)

    def test_refuses_an_unknown_key(
        self,
        verify_api_key: VerifyApiKey,
        api_key_repository: FakeApiKeyRepository,
    ) -> None:
        api_key_repository.add(build_api_key())

        with pytest.raises(InvalidApiKeyError):
            verify_api_key.execute(KEY)

    def test_refuses_a_revoked_key(
        self,
        verify_api_key: VerifyApiKey,
        api_key_repository: FakeApiKeyRepository,
        token_hasher: FakeTokenHasher,
        public_api_token_creator: FakePublicApiTokenCreator,
    ) -> None:
        api_key_repository.add(
            build_api_key(key_hash=token_hasher.hash(KEY), revoked_at=datetime.now(UTC))
        )

        with pytest.raises(InvalidApiKeyError):
            verify_api_key.execute(KEY)
        assert public_api_token_creator.calls == []

    def test_refuses_an_expired_key(
        self,
        verify_api_key: VerifyApiKey,
        api_key_repository: FakeApiKeyRepository,
        token_hasher: FakeTokenHasher,
    ) -> None:
        api_key_repository.add(
            build_api_key(
                key_hash=token_hasher.hash(KEY),
                created_at=datetime.now(UTC) - API_KEY_LIFETIME * 2,
            )
        )

        with pytest.raises(InvalidApiKeyError):
            verify_api_key.execute(KEY)

    def test_never_matches_the_stored_hash_given_as_a_key(
        self,
        verify_api_key: VerifyApiKey,
        api_key_repository: FakeApiKeyRepository,
        token_hasher: FakeTokenHasher,
    ) -> None:
        # Someone who read the database must not be able to use the hashes.
        stored_hash: str = token_hasher.hash(KEY)
        api_key_repository.add(build_api_key(key_hash=stored_hash, account_id=uuid4()))

        with pytest.raises(InvalidApiKeyError):
            verify_api_key.execute(stored_hash)
