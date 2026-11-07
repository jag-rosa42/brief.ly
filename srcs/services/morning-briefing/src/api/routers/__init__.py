from fastapi import APIRouter

from src.api.routers.briefing.router import router as briefing_router
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


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
# Endpoints the frontend reaches through the gateway.
#
# There is no "/api" prefix here: the browser calls /api/morning-briefing/<path>
# and the gateway removes "/api/morning-briefing" before forwarding, so this
# service only ever sees its own paths.
#
# Example:
#   browser: GET /api/morning-briefing/briefing
#   service: GET /briefing
# ---------------------------------------------------------------------------
api_routers = APIRouter()
api_routers.include_router(briefing_router)
