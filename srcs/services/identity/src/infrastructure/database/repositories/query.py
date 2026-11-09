from collections.abc import Callable

from sqlalchemy import Select
from sqlalchemy.orm import Session


def one_or_none[Model, Entity](
    session: Session,
    statement: Select[tuple[Model]],
    to_domain: Callable[[Model], Entity],
) -> Entity | None:
    """Run a query that matches at most one row, and return it as an entity.

    Used by every repository's finders (find_by_id, find_by_email, find_by_hash, ...)

    Usage in a repository:

        statement = select(AccountModel).where(AccountModel.id == account_id)
        return one_or_none(self._session, statement, self._to_domain)

    Returns:
        The entity built by `to_domain`, or None when no row matches.

    Raises:
        MultipleResultsFound: More than one row matched. This is not "take
        the first one": it means the query (or a missing unique
        constraint) is wrong, and hiding it would return an arbitrary
        row. That's why this function isn't called `first_or_none`.
    """
    model: Model | None = session.execute(statement).scalar_one_or_none()
    if model is None:
        return None
    return to_domain(model)
