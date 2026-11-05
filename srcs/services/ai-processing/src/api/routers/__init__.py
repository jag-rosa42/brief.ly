from fastapi import APIRouter

from src.api.routers.health.router import router as health_router

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

# No business routes: AI Processing is a worker that writes summaries to
# Content Management (ADR-0010). Nobody calls it during a request.
