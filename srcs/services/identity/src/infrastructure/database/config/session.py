# Import the Session class and the sessionmaker that creates Session objects.
from sqlalchemy.orm import Session, sessionmaker

# Import the Engine.
# The Engine knows how to connect to PostgreSQL.
from src.infrastructure.database.config import engine

"""
Relationship between the main SQLAlchemy objects:

Settings
    │
    ▼
Database URL
    │
    ▼
Engine
    │
    ▼
SessionLocal (factory)
    │
    ▼
Session
    │
    ▼
ORM Models
"""
"""
SessionLocal is a factory that creates new SQLAlchemy Session objects.

Each Session represents one unit of work with the database (typically one
HTTP request in a FastAPI application).

A Session is not the same as a database transaction.
Instead, it manages one or more transactions during its lifetime.

A Session is responsible for:
- Tracking ORM objects that are loaded or added.
- Detecting changes made to those objects.
- Sending SQL statements to the database when needed.
- Managing the underlying database connection.
- Opening, committing, and rolling back database transactions.

In a FastAPI application, we usually create one Session per request.
"""
SessionLocal = sessionmaker(
    # The Engine this Session will use to communicate with the database.
    bind=engine,

    # The class used when creating new Session objects.
    # Explicitly specifying Session is optional because it is the default.
    class_=Session,

    # Prevent SQLAlchemy from automatically flushing pending INSERT,
    # UPDATE, and DELETE statements before executing queries.
    #
    # Changes are still flushed automatically when commit() is called.
    autoflush=False,

    # Keep ORM objects' attributes available after commit().
    #
    # If True (the default), SQLAlchemy expires object state after every
    # commit, causing attribute access to reload data from the database.
    expire_on_commit=False,
)
