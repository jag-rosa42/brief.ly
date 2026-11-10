from uuid import uuid4

from src.application.use_cases.api_keys.revoke_api_key import RevokeApiKey
from src.domain.entities.api_key import ApiKey
from tests.fixtures.api_keys import FakeApiKeyRepository
from tests.fixtures.factory import build_api_key
from tests.fixtures.unit_of_work import FakeUnitOfWork


class TestRevokeApiKey:
    def test_revokes_the_key_and_commits(
        self,
        revoke_api_key: RevokeApiKey,
        api_key_repository: FakeApiKeyRepository,
        uow: FakeUnitOfWork,
    ) -> None:
        api_key = build_api_key()
        api_key_repository.add(api_key)

        revoke_api_key.execute(account_id=api_key.account_id, api_key_id=api_key.id)

        assert api_key_repository.get(api_key.id).is_revoked() is True
        assert uow.commit_count == 1

    def test_is_idempotent(
        self,
        revoke_api_key: RevokeApiKey,
        api_key_repository: FakeApiKeyRepository,
        uow: FakeUnitOfWork,
    ) -> None:
        api_key = build_api_key()
        api_key_repository.add(api_key)
        revoke_api_key.execute(account_id=api_key.account_id, api_key_id=api_key.id)
        first_revoked_at = api_key_repository.get(api_key.id).revoked_at

        revoke_api_key.execute(account_id=api_key.account_id, api_key_id=api_key.id)

        assert api_key_repository.get(api_key.id).revoked_at == first_revoked_at
        assert uow.commit_count == 1

    def test_does_nothing_for_an_unknown_key(
        self,
        revoke_api_key: RevokeApiKey,
        uow: FakeUnitOfWork,
    ) -> None:
        revoke_api_key.execute(account_id=uuid4(), api_key_id=uuid4())

        assert uow.committed is False

    def test_never_revokes_another_accounts_key(
        self,
        revoke_api_key: RevokeApiKey,
        api_key_repository: FakeApiKeyRepository,
        uow: FakeUnitOfWork,
    ) -> None:
        api_key = build_api_key()
        api_key_repository.add(api_key)

        revoke_api_key.execute(account_id=uuid4(), api_key_id=api_key.id)

        assert api_key_repository.get(api_key.id).is_revoked() is False
        assert uow.committed is False

    def test_does_not_commit_when_revoked_concurrently(
        self,
        uow: FakeUnitOfWork,
    ) -> None:
        class RevokedMeanwhile(FakeApiKeyRepository):
            # Another request revoked the key between our read and our write:
            # the compare-and-set update matches no row.
            def update(self, api_key: ApiKey) -> bool:
                return False

        api_key_repository = RevokedMeanwhile()
        api_key = build_api_key()
        api_key_repository.add(api_key)

        RevokeApiKey(uow, api_key_repository).execute(
            account_id=api_key.account_id, api_key_id=api_key.id
        )

        assert uow.committed is False
