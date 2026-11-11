from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared_auth import (
    PublicDocument,
    install_authentication,
    install_public_docs_page,
    install_public_openapi,
    public_openapi_path,
)
from shared_errors import register_shared_exception_handlers

from src.api.dependencies.clients import close_clients
from src.api.errors.handlers import register_domain_exception_handlers
from src.api.routers import api_routers, internal_routers, public_routers, root_routers
from src.infrastructure.config.app import app_settings
from src.infrastructure.config.auth import auth_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    # FastAPI's startup/shutdown hook: it must be an async context manager
    # (the older @app.on_event is deprecated), even in an app of sync routes.
    yield
    # When the service stops: close the connections to other services.
    close_clients()


def create_app() -> FastAPI:
    app = FastAPI(title=app_settings.PROJECT_NAME, lifespan=lifespan)

    # Allow the configured frontend origin(s) to call this API from the browser.
    # Without this, the browser blocks cross-origin requests
    app.add_middleware(
        middleware_class=CORSMiddleware,
        allow_origins=app_settings.BACKEND_CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(root_routers)
    app.include_router(api_routers)
    app.include_router(internal_routers)
    app.include_router(public_routers)
    register_shared_exception_handlers(app)
    register_domain_exception_handlers(app)
    install_authentication(app, auth_settings, public_api=True)

    # Public API documentation (ADR-0009), readable without a key:
    # - this service's document: GET /public/v1/openapi/personalization.json
    install_public_openapi(
        app,
        public_routers,
        service_name="personalization",
        title="Transcendence public API: profile, topics and saved articles",
    )
    # - the page for every service's document: GET /public/v1/docs
    #   (Personalization hosts it; Morning Briefing serves its own document).
    install_public_docs_page(
        app,
        documents=[
            PublicDocument("Personalization", public_openapi_path("personalization")),
            PublicDocument("Morning Briefing", public_openapi_path("morning-briefing")),
        ],
    )

    return app


app: FastAPI = create_app()
