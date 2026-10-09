"""Health and root API endpoints for the application.

Provides the root endpoint and a database connectivity health check
for container/orchestrator probes.
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from src.api.dependencies import SessionDep

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: SessionDep):
    """
    Report whether the app can talk to the database.

    Meant to back an orchestrator probe (Docker/Compose HEALTHCHECK,
    Kubernetes liveness/readiness) the same way a container's own
    HEALTHCHECK command verifies the process is actually working.
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc

    return {"status": "ok", "database": "ok"}
