from dataclasses import FrozenInstanceError

import pytest

from src.domain.exception import InvalidEmail
from src.domain.value_objects.email import Email


def test_email_accepts_valid_email() -> None:
    email: Email = Email("john.doe@example.com")
    assert email.value == "john.doe@example.com"


def test_email_normalizes_email() -> None:
    email: Email = Email("john.doe@Example.COM")
    assert email.value == "john.doe@example.com"


def test_email_reject_invalid_email() -> None:
    with pytest.raises(InvalidEmail):
        Email("not-an-email")


def test_email_reject_empty_email() -> None:
    with pytest.raises(InvalidEmail):
        Email("")


def test_email_is_immutable() -> None:
    email: Email = Email("john.doe@example.com")

    with pytest.raises(FrozenInstanceError):
        email.value = "jane.doe@example.com"  # ty: ignore[invalid-assignment]
