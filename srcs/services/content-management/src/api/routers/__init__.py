from fastapi import APIRouter

from src.api.routers.articles.router import router as article_router
from src.api.routers.health.router import router as health_router
from src.api.routers.ingestion_runs.router import router as ingestion_run_router
from src.api.routers.topics.router import router as topic_router

# ---------------------------------------------------------------------------
# Root-level endpoints
# ---------------------------------------------------------------------------
# Endpoints registered here are exposed directly at the application root,
# without the /api prefix.
#
# Example:
#   health_router -> GET /health
# ---------------------------------------------------------------------------
root_routers = APIRouter()
root_routers.include_router(health_router)

# ---------------------------------------------------------------------------
# Internal API endpoints
# ---------------------------------------------------------------------------
# All business endpoints exposed by this service are internal and versioned
# under /internal/v1. Individual routers define only their resource prefix,
# such as /topics and /articles.
# ---------------------------------------------------------------------------

api_routers = APIRouter(prefix="/internal/v1")
api_routers.include_router(article_router)
api_routers.include_router(ingestion_run_router)
api_routers.include_router(topic_router)
