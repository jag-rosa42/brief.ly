from fastapi import APIRouter
from shared_auth import PUBLIC_API_RESPONSES

from src.api.routers.health.router import router as health_router
from src.api.routers.internal_profile.router import router as internal_profile_router
from src.api.routers.profile.router import router as profile_router
from src.api.routers.public_profile.router import router as public_profile_router
from src.api.routers.public_saved_articles.router import (
    router as public_saved_articles_router,
)
from src.api.routers.public_topics.router import router as public_topics_router
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

# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------
# The Public API (ADR-0009): third-party programs, with an API key. The
# gateway checks the key (ForwardAuth to Identity) and forwards the request
# with a public API token, without stripping the path: the service sees
# /public/v1/... as the program sent it.
#
# Same use cases as the frontend routes; only the caller and the scopes
# differ. Only these routes go into the public OpenAPI document.
#
# Example:
#   program: GET https://<host>/public/v1/me/profile   (X-API-Key: tr_...)
#   service: GET /public/v1/me/profile                 (Authorization: Bearer ...)
# ---------------------------------------------------------------------------
public_routers = APIRouter(prefix="/public/v1", responses=PUBLIC_API_RESPONSES)
public_routers.include_router(public_profile_router)
public_routers.include_router(public_saved_articles_router)
public_routers.include_router(public_topics_router)
