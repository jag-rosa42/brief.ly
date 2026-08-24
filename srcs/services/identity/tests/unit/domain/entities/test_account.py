import datetime
import uuid

from src.domain.entities.account import Account
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash


def test_account_can_be_created() -> None:
    account_id: uuid.UUID = uuid.uuid4()
    email: Email = Email("john.doe@example.com")
    password_hash = PasswordHash("super-secret")
    created_at: datetime.datetime = datetime.datetime.now(datetime.UTC)

    account = Account(
        account_id,
        email,
        password_hash,
        created_at,
    )

    assert account.id == account_id
    assert account.email == email
    assert account.password_hash == password_hash
    assert account.created_at == created_at


def test_account_preserves_values_objetcs() -> None:
    account_id: uuid.UUID = uuid.uuid4()
    email: Email = Email("john.doe@example.com")
    password_hash = PasswordHash("super-secret")
    created_at: datetime.datetime = datetime.datetime.now(datetime.UTC)

    account = Account(
        account_id,
        email,
        password_hash,
        created_at,
    )

    assert isinstance(account.email, Email)
    assert isinstance(account.password_hash, PasswordHash)
