from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.application.use_cases.api_keys.list_api_keys import ListApiKeys
from src.domain.entities.api_key import API_KEY_LIFETIME
from tests.fixtures.api_keys import FakeApiKeyRepository
from tests.fixtures.factory import build_api_key


class TestListApiKeys:
    def test_returns_an_empty_list_without_keys(self, list_api_keys: ListApiKeys) -> None:
        assert list_api_keys.execute(uuid4()) == []

    def test_returns_the_active_keys_newest_first(
        self,
        list_api_keys: ListApiKeys,
        api_key_repository: FakeApiKeyRepository,
    ) -> None:
        account_id = uuid4()
        now = datetime.now(UTC)
        older = build_api_key(account_id=account_id, created_at=now - timedelta(hours=2))
        newer = build_api_key(account_id=account_id, created_at=now - timedelta(hours=1))
        api_key_repository.add(older)
        api_key_repository.add(newer)

        result = list_api_keys.execute(account_id)

        assert [api_key.id for api_key in result] == [newer.id, older.id]

    def test_leaves_out_revoked_expired_and_other_accounts_keys(
        self,
        list_api_keys: ListApiKeys,
        api_key_repository: FakeApiKeyRepository,
    ) -> None:
        account_id = uuid4()
        now = datetime.now(UTC)
        active = build_api_key(account_id=account_id)
        api_key_repository.add(active)
        api_key_repository.add(build_api_key(account_id=account_id, revoked_at=now))
        api_key_repository.add(
            build_api_key(account_id=account_id, created_at=now - API_KEY_LIFETIME * 2)
        )
        api_key_repository.add(build_api_key(account_id=uuid4()))

        result = list_api_keys.execute(account_id)

        assert [api_key.id for api_key in result] == [active.id]
