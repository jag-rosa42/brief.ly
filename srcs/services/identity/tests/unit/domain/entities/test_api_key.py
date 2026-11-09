from datetime import UTC, datetime, timedelta

from src.domain.entities.api_key import API_KEY_LIFETIME, ApiKey
from tests.fixtures.factory import build_api_key


class TestApiKey:
    def test_a_new_key_is_active(self) -> None:
        api_key: ApiKey = build_api_key()

        assert api_key.is_active(datetime.now(UTC)) is True

    def test_is_expired_from_its_expiry_date(self) -> None:
        created_at = datetime.now(UTC)
        api_key: ApiKey = build_api_key(created_at=created_at)

        assert api_key.expires_at == created_at + API_KEY_LIFETIME
        assert api_key.is_expired(api_key.expires_at - timedelta(seconds=1)) is False
        # The expiry instant itself is already expired, like refresh tokens.
        assert api_key.is_expired(api_key.expires_at) is True
        assert api_key.is_active(api_key.expires_at) is False

    def test_revoke_makes_the_key_inactive(self) -> None:
        api_key: ApiKey = build_api_key()
        now = datetime.now(UTC)

        api_key.revoke(now)

        assert api_key.is_revoked() is True
        assert api_key.revoked_at == now
        assert api_key.is_active(now) is False

    def test_revoke_keeps_the_first_revocation_date(self) -> None:
        api_key: ApiKey = build_api_key()
        first = datetime.now(UTC)

        api_key.revoke(first)
        api_key.revoke(first + timedelta(minutes=1))

        assert api_key.revoked_at == first
