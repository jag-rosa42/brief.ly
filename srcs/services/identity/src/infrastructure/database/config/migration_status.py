"""
Display the status of Alembic migrations, similar to Rails'
`rails db:migrate:status`.

Why this script exists
----------------------
Alembic provides commands such as:

    alembic current
    alembic heads
    alembic history

However, it doesn't provide a single command that lists every migration and
whether it has been applied ("up") or is still pending ("down") like Rails.

This script fills that gap by:

1. Reading the current revision from the `alembic_version` table.
2. Walking backwards through the migration history to determine every applied
   revision.
3. Listing every migration in chronological order with an "up" or "down"
   status.

Example output:

    Current revision: 3a9c12e4f1d

    Status Revision       Message
    ----------------------------------------------------------------------
    up     1b7d8e3f4c5a    initial
    up     2ac8f2d90a9b    create users
    up     3a9c12e4f1d     create posts
    down   4d2f8c1d8b8f    add comments

Notes
-----
This utility assumes a single, linear Alembic migration history.

If your project introduces migration branches (multiple heads), this script
will raise an exception instead of attempting to resolve them automatically.

Usage
-----
Run from the project root:

    uv run python -m app.db.migration_status

or

    python -m app.db.migration_status
"""

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from src.infrastructure.database.config import engine


def get_current_revision() -> str | None:
    """
    Collect every applied revision from the current revision back to the base.

    The returned set is later used to determine whether each migration should
    be displayed as "up" or "down".
    """
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()


def get_applied_revisions(
    script: ScriptDirectory,
    current_revision: str | None,
) -> set[str]:
    """Return all applied revisions from the current revision back to the base."""
    if current_revision is None:
        return set()

    applied: set[str] = set()
    revision = script.get_revision(current_revision)

    while revision is not None:
        applied.add(revision.revision)

        parent = revision.down_revision

        if parent is None:
            break

        if not isinstance(parent, str):
            raise RuntimeError(
                "This script doesn't support Alembic migration branches."
            )

        revision = script.get_revision(parent)

    return applied


def main() -> None:
    """Print a migration status table."""
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    current = get_current_revision()
    applied = get_applied_revisions(script, current)

    print()
    print(f"Current revision: {current or '<base>'}")
    print()

    print(f"{'Status':<6} {'Revision':<14} Message")
    print("-" * 70)

    revisions = list(script.walk_revisions())
    revisions.reverse()  # oldest → newest

    for revision in revisions:
        status = "up" if revision.revision in applied else "down"

        print(f"{status:<6}{revision.revision:<14}{revision.doc or ''}")


if __name__ == "__main__":
    main()
