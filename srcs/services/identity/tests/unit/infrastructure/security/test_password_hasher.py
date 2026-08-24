import pytest

from src.domain.value_objects.password_hash import PasswordHash
from src.infrastructure.security.password_hasher import PwdlibPasswordHasher


@pytest.fixture
def hasher() -> PwdlibPasswordHasher:
    return PwdlibPasswordHasher()


def test_hasher_returns_hashed_password(hasher: PwdlibPasswordHasher) -> None:
    raw_password: str = "super-secret"
    password_hashed: PasswordHash = hasher.hash(raw_password)

    assert isinstance(password_hashed, PasswordHash)
    assert password_hashed.value != raw_password


def test_hasher_can_be_verified(hasher: PwdlibPasswordHasher) -> None:
    raw_password: str = "super-secret"
    password_hashed: PasswordHash = hasher.hash(raw_password)

    assert hasher.verify(raw_password, password_hashed)


def test_hasher_rejects_wrong_password(hasher: PwdlibPasswordHasher) -> None:
    raw_password: str = "super-secret"
    password_hashed: PasswordHash = hasher.hash(raw_password)
    wrong_password: str = "wrong-super-secret"

    assert not hasher.verify(wrong_password, password_hashed)


def test_hasher_produces_different_result_for_same_password(
    hasher: PwdlibPasswordHasher,
) -> None:
    raw_password: str = "super-secret"
    first_password_hashed: PasswordHash = hasher.hash(raw_password)
    second_password_hashed: PasswordHash = hasher.hash(raw_password)

    assert first_password_hashed != second_password_hashed
