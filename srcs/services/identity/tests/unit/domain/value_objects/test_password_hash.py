from dataclasses import FrozenInstanceError

import pytest

from src.domain.exception import InvalidPasswordHash
from src.domain.value_objects.password_hash import PasswordHash


def test_password_hash_can_be_created() -> None:
    password_value: str = "123456"
    password_hash: PasswordHash = PasswordHash(password_value)
    assert password_hash.value == password_value


def test_password_hash_can_not_be_empty() -> None:
    with pytest.raises(InvalidPasswordHash):
        PasswordHash("")


def test_password_hash_is_immutable() -> None:
    password_hash: PasswordHash = PasswordHash("123456")

    with pytest.raises(FrozenInstanceError):
        password_hash.value = "abcdef"  # ty: ignore[invalid-assignment]
