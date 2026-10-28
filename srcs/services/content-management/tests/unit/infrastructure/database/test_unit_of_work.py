from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_commits_the_session() -> None:
    session = Mock()

    SqlAlchemyUnitOfWork(session).commit()

    session.commit.assert_called_once_with()


def test_rolls_back_when_commit_fails() -> None:
    session = Mock()
    session.commit.side_effect = SQLAlchemyError("commit failed")

    with pytest.raises(SQLAlchemyError, match="commit failed"):
        SqlAlchemyUnitOfWork(session).commit()

    session.rollback.assert_called_once_with()


def test_leaving_the_context_rolls_back_uncommitted_changes() -> None:
    session = Mock()

    with SqlAlchemyUnitOfWork(session):
        pass

    session.rollback.assert_called_once_with()
