"""one_or_none(), the helper every repository's finders share.

On the accounts table, but nothing here is about accounts: any model and
any to_domain function would do.
"""

import pytest
from sqlalchemy import Select, select
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import Session

from src.domain.entities.account import Account
from src.domain.value_objects.password_hash import PasswordHash
from src.infrastructure.database.models.account import Account as AccountModel
from src.infrastructure.database.repositories.query import one_or_none
from src.infrastructure.database.repositories.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)
from tests.fixtures.factory import build_account


def _convert(model: AccountModel) -> str:
    """A to_domain stand-in: it shows one_or_none returns what this returns."""
    return f"converted:{model.email}"


def _save(db_session: Session, email: str) -> Account:
    account: Account = build_account(email=email, password_hash=PasswordHash("x"))
    SqlAlchemyAccountRepository(db_session).save(account)
    db_session.flush()
    return account


class TestOneOrNone:
    def test_returns_none_when_no_row_matches(self, db_session: Session) -> None:
        statement: Select[tuple[AccountModel]] = select(AccountModel).where(
            AccountModel.email == "nobody@example.com"
        )

        assert one_or_none(db_session, statement, _convert) is None

    def test_returns_the_row_converted_by_to_domain(self, db_session: Session) -> None:
        account: Account = _save(db_session, "one@example.com")
        statement: Select[tuple[AccountModel]] = select(AccountModel).where(
            AccountModel.id == account.id
        )

        result: str | None = one_or_none(db_session, statement, _convert)

        assert result == "converted:one@example.com"

    def test_raises_when_more_than_one_row_matches(self, db_session: Session) -> None:
        # Not "the first one": two rows mean the query is wrong.
        _save(db_session, "first@example.com")
        _save(db_session, "second@example.com")
        statement: Select[tuple[AccountModel]] = select(AccountModel).where(
            AccountModel.email.in_(["first@example.com", "second@example.com"])
        )

        with pytest.raises(MultipleResultsFound):
            one_or_none(db_session, statement, _convert)
