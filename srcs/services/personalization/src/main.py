from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared_auth import install_authentication
from shared_errors import register_shared_exception_handlers

from src.api.errors.handlers import register_domain_exception_handlers
from src.api.routers import api_routers, internal_routers, root_routers
from src.infrastructure.config.app import app_settings
from src.infrastructure.config.auth import auth_settings
from src.infrastructure.metrics.http import configure_http_metrics


def create_app() -> FastAPI:
    app = FastAPI(title=app_settings.PROJECT_NAME)

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
    register_shared_exception_handlers(app)
    register_domain_exception_handlers(app)
    install_authentication(app, auth_settings, public_api=True)

    configure_http_metrics(app)

    return app


app: FastAPI = create_app()
