from fastapi import APIRouter
from shared_auth import PUBLIC_API_RESPONSES

from src.api.routers.briefing.router import router as briefing_router
from src.api.routers.health.router import router as health_router
from src.api.routers.public_briefing.router import router as public_briefing_router

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

# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------
# The Public API (ADR-0009): third-party programs, with an API key. The
# gateway checks the key (ForwardAuth to Identity) and forwards the request
# with a public API token, without stripping the path.
#
# Example:
#   program: GET https://<host>/public/v1/morning-briefing   (X-API-Key: tr_...)
#   service: GET /public/v1/morning-briefing                 (Authorization: Bearer ...)
# ---------------------------------------------------------------------------
public_routers = APIRouter(prefix="/public/v1", responses=PUBLIC_API_RESPONSES)
public_routers.include_router(public_briefing_router)
