from fastapi import APIRouter

from src.api.routers.health.router import router as health_router
from src.api.routers.internal_profile.router import router as internal_profile_router
from src.api.routers.profile.router import router as profile_router
from src.api.routers.saved_articles.router import router as saved_articles_router
from src.api.routers.topics.router import router as topics_router

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
# There is no "/api" prefix here: the browser calls /api/personalization/<path>
# and the gateway removes "/api/personalization" before forwarding, so this
# service only ever sees its own paths.
#
# Example:
#   browser: GET /api/personalization/me/profile
#   service: GET /me/profile
# ---------------------------------------------------------------------------
api_routers = APIRouter()
api_routers.include_router(profile_router)
api_routers.include_router(saved_articles_router)
api_routers.include_router(topics_router)

# ---------------------------------------------------------------------------
# Internal endpoints
# ---------------------------------------------------------------------------
# Endpoints called by the other services, never through the gateway.
# They are versioned under /internal/v1, and each router only defines
# its resource prefix.
#
# Example:
#   Morning Briefing: GET /internal/v1/me/profile
# ---------------------------------------------------------------------------
internal_routers = APIRouter(prefix="/internal/v1")
internal_routers.include_router(internal_profile_router)
