from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.infrastructure.database.config import SessionFactory


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
