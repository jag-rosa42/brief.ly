from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from src.domain.entities.refresh_token import RefreshToken
from tests.fixtures.factory import build_refresh_token


class TestRefreshToken:
    def test_new_refresh_token_is_not_revoked(self) -> None:
        token: RefreshToken = build_refresh_token()

        assert token.is_revoked() is False
        assert token.revoked_at is None
        assert token.replaced_by is None

    def test_revoke_marks_the_token_and_records_its_replacement(self) -> None:
        token: RefreshToken = build_refresh_token()
        replacement_id: UUID = uuid4()
        now: datetime = datetime.now(UTC)

        token.revoke(now, replaced_by=replacement_id)

        assert token.is_revoked() is True
        assert token.revoked_at == now
        assert token.replaced_by == replacement_id

    def test_revoke_without_replacement_leaves_replaced_by_empty(self) -> None:
        token: RefreshToken = build_refresh_token()

        token.revoke(datetime.now(UTC))

        assert token.is_revoked() is True
        assert token.replaced_by is None

    def test_revoke_is_idempotent(self) -> None:
        token: RefreshToken = build_refresh_token()
        first_revocation: datetime = datetime.now(UTC)
        replacement_id: UUID = uuid4()

        token.revoke(first_revocation, replaced_by=replacement_id)

        token.revoke(first_revocation + timedelta(hours=1), replaced_by=uuid4())

        assert token.revoked_at == first_revocation
        assert token.replaced_by == replacement_id

    @pytest.mark.parametrize(
        ("offset", "expected"),
        [
            (timedelta(seconds=-1), True),
            (timedelta(0), True),  # expires exactly at expires_at
            (timedelta(seconds=1), False),
        ],
    )
    def test_is_expired_boundaries(
        self,
        offset: timedelta,
        expected: bool,
    ) -> None:
        now = datetime.now(UTC)
        token = build_refresh_token(expires_at=now + offset)

        assert token.is_expired(now) is expected

    def test_was_rotated_is_true_once_replaced(self) -> None:
        token = build_refresh_token()

        token.revoke(datetime.now(UTC), replaced_by=uuid4())

        assert token.was_rotated() is True

    def test_was_rotated_is_false_when_revoked_without_replacement(self) -> None:
        token = build_refresh_token()

        token.revoke(datetime.now(UTC))  # e.g. a logout

        assert token.is_revoked() is True
        assert token.was_rotated() is False

    def test_was_rotated_is_false_for_an_active_token(self) -> None:
        assert build_refresh_token().was_rotated() is False

    def test_is_active_until_revoked(self) -> None:
        # Given by RevocableMixin, like for API keys.
        token = build_refresh_token()
        now = datetime.now(UTC)

        assert token.is_active(now) is True
        token.revoke(now)
        assert token.is_active(now) is False
