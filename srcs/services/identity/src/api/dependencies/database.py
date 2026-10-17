from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.port.unit_of_work import UnitOfWork
from src.infrastructure.database.config import SessionFactory
from src.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def get_db() -> Generator[Session]:
    """
    FastAPI dependency that provides one SQLAlchemy Session per request.

    The Session is automatically closed after the request finishes,
    even if an exception occurs.
    """

    # Create a new Session for this request.
    db = SessionFactory()

    try:
        # Pause here and give the Session to the route handler.
        #
        # FastAPI resumes execution after the endpoint returns,
        # allowing us to perform cleanup.
        yield db
    finally:
        # Return the database connection to SQLAlchemy's connection pool.
        #
        # close() also rolls back any transaction still open. The first query
        # of a request opens one implicitly ("BEGIN (implicit)" in the logs),
        # even for a read. So a read-only request such as GET /accounts/me
        # always ends with a ROLLBACK: that is expected, there is nothing to
        # commit, and the connection goes back to the pool clean.
        # Requests that commit through the UnitOfWork have no transaction left
        # open here, so no ROLLBACK is logged for them.
        #
        # The Session should not be reused after it is closed.
        db.close()


# Reusable dependency annotation.
#
# Instead of writing:
#
#     db: Session = Depends(get_db)
#
# every time, routes can simply write:
#
#     db: SessionDep
SessionDep = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------------------------
# Unit of Work
# ---------------------------------------------------------------------------
# FastAPI caches dependencies per request: SessionDep resolves to the SAME
# Session for the UnitOfWork and for every repository of the request.
#
# This is what makes uow.commit() include the changes staged by the
# repositories. Never build a repository or a UnitOfWork from another Session.
def get_unit_of_work(session: SessionDep) -> UnitOfWork:
    return SqlAlchemyUnitOfWork(session)


UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]
