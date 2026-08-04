from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from src.api.dependencies import SessionDep
from src.infrastructure.database.config import settings

app = FastAPI(title=settings.PROJECT_NAME)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check(db: SessionDep):
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
