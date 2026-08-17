from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.api.dependencies import SessionDep
from src.api.routers.router import api_router
from src.infrastructure.database.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Allow the configured frontend origin(s) to call this API from the browser.
# Without this, the browser blocks cross-origin requests
app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

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
