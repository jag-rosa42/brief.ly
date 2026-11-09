from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from src.domain.entities.revocable import RevocableMixin


@dataclass
class Credential(RevocableMixin):
    """The smallest entity using the mixin: only the two fields it needs."""

    expires_at: datetime
    revoked_at: datetime | None = None


def build_credential(expires_in: timedelta = timedelta(hours=1)) -> Credential:
    return Credential(expires_at=datetime.now(UTC) + expires_in)


class TestRevocableMixin:
    def test_a_new_credential_is_active(self) -> None:
        credential = build_credential()

        assert credential.is_revoked() is False
        assert credential.is_active(datetime.now(UTC)) is True

    @pytest.mark.parametrize(
        ("offset", "expected"),
        [
            (timedelta(seconds=-1), False),
            (timedelta(0), True),  # expired at expires_at itself
            (timedelta(seconds=1), True),
        ],
    )
    def test_is_expired_boundaries(self, offset: timedelta, expected: bool) -> None:
        credential = build_credential()

        assert credential.is_expired(credential.expires_at + offset) is expected

    def test_an_expired_credential_is_not_active(self) -> None:
        credential = build_credential()

        assert credential.is_active(credential.expires_at) is False

    def test_revoke_makes_it_inactive(self) -> None:
        credential = build_credential()
        now = datetime.now(UTC)

        credential.revoke(now)

        assert credential.is_revoked() is True
        assert credential.revoked_at == now
        assert credential.is_active(now) is False

    def test_revoke_keeps_the_first_revocation_date(self) -> None:
        credential = build_credential()
        first = datetime.now(UTC)

        credential.revoke(first)
        credential.revoke(first + timedelta(minutes=1))

        assert credential.revoked_at == first
