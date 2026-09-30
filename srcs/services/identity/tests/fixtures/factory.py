from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.domain.entities.account import Account
from src.domain.entities.refresh_token import RefreshToken
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash

# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------

DEFAULT_ACCOUNT_EMAIL: str = "john.doe@example.com"
DEFAULT_ACCOUNT_PASSWORD: str = "super-secret"


def build_account(
    *,
    email: str,
    password_hash: PasswordHash,
    account_id: UUID | None = None,
    created_at: datetime | None = None,
) -> Account:
    """Build an Account for tests.

    password_hash is required and deliberately has no plaintext shortcut:
    - repository/schema tests that don't verify passwords can pass
      PasswordHash("anything") directly.
    - anything that later calls password_hasher.verify(...) (login, etc.)
      must pass password_hasher.hash(plaintext) so the hash is real.
    """
    return Account(
        id=account_id or uuid4(),
        email=Email(email),
        password_hash=password_hash,
        created_at=created_at or datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Refresh-Token
# ---------------------------------------------------------------------------


def build_refresh_token(
    *,
    account_id: UUID | None = None,
    refresh_token_id: UUID | None = None,
    token_hash: str | None = None,
    expires_at: datetime | None = None,
    created_at: datetime | None = None,
    revoked_at: datetime | None = None,
    replaced_by: UUID | None = None,
) -> RefreshToken:
    """Build a RefreshToken for tests.

    account_id defaults to a throwaway UUID for entity-level tests that
    don't touch a real account (is_expired, was_rotated, ...). Repository
    tests that hit a real foreign key must pass an actual persisted
    account_id explicitly.
    """
    now = datetime.now(UTC)
    return RefreshToken(
        id=refresh_token_id or uuid4(),
        account_id=account_id or uuid4(),
        token_hash=token_hash or f"hash-{uuid4()}",
        expires_at=expires_at or now + timedelta(days=30),
        created_at=created_at or now,
        revoked_at=revoked_at,
        replaced_by=replaced_by,
    )
