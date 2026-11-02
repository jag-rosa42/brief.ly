"""Startup wiring: build the authenticator once and attach it to the app.

This is the package's composition root: the one place where the concrete
objects (the JWT verifier, the authenticator) are built from the settings and
connected. It runs once, when the service starts:

    install_authentication(app, auth_settings)   # in the service's main.py
    install_authentication(app, auth_settings, public_api=True)  # public API

Everything that runs on each request is in dependencies.py.
"""

from fastapi import FastAPI, Request

from shared_auth.api.errors.handlers import configure_exception_handlers
from shared_auth.application.authenticator import Authenticator
from shared_auth.infrastructure.settings import AuthSettings
from shared_auth.infrastructure.tokens.jwt_token_verifier import JWTTokenVerifier


def build_authenticator(settings: AuthSettings) -> Authenticator:
    """Build the authenticator a service uses, from its environment settings."""
    verifier = JWTTokenVerifier(
        public_key_pem=settings.JWT_PUBLIC_KEY,
        issuer=settings.JWT_ISSUER,
        audiences=settings.accepted_audiences,
    )
    return Authenticator(
        verifier,
        access_audience=settings.JWT_ACCESS_AUDIENCE,
        service_audience=settings.JWT_SERVICE_AUDIENCE,
        public_api_audience=settings.JWT_PUBLIC_API_AUDIENCE,
    )


def install_authentication(
    app: FastAPI,
    settings: AuthSettings,
    *,
    public_api: bool = False,
) -> Authenticator:
    """Build the authenticator once, attach it, and register the error handlers.

    Called when the app is created, so a missing or invalid public key makes
    the service crash at startup with a clear error, instead of answering 500
    to the first request.

    public_api=True: the service accepts public API tokens, on its public
    routes or forwarded by another service (ADR-0009). Then
    JWT_PUBLIC_API_AUDIENCE is required, and checked here for the same reason.

    The handlers are registered here so a service cannot forget them: without
    them, every InvalidTokenError would reach shared_errors' catch-all handler
    and become a 500 instead of a 401.
    """
    if public_api and settings.JWT_PUBLIC_API_AUDIENCE is None:
        raise ValueError("public_api=True requires JWT_PUBLIC_API_AUDIENCE")
    authenticator: Authenticator = build_authenticator(settings)
    app.state.authenticator = authenticator
    configure_exception_handlers(app)
    return authenticator


def get_authenticator(request: Request) -> Authenticator:
    authenticator: Authenticator | None = getattr(
        request.app.state,
        "authenticator",
        None,
    )
    if authenticator is None:
        raise RuntimeError("install_authentication(app, settings) was not called")
    return authenticator
