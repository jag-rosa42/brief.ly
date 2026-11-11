"""One public OpenAPI document per service: its public routes, and nothing else."""

from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from shared_auth.api.public_docs.paths import (
    API_KEY_HEADER_NAME,
    API_KEY_SECURITY_SCHEME,
    PUBLIC_API_PREFIX,
    public_openapi_path,
)
from shared_auth.api.public_docs.responses import (
    IP_RATE_LIMIT_BURST,
    IP_RATE_LIMIT_PER_SECOND,
    KEY_RATE_LIMIT_BURST,
    KEY_RATE_LIMIT_PER_SECOND,
)

# Shown at the top of every public document (Markdown), under the service's
# own description: developers read the limits before they hit them.
RATE_LIMITS_DESCRIPTION: str = (
    "**Rate limits.** "
    f"{KEY_RATE_LIMIT_PER_SECOND} requests per second per API key "
    f"(bursts of up to {KEY_RATE_LIMIT_BURST}), "
    f"{IP_RATE_LIMIT_PER_SECOND} per second per IP address "
    f"(bursts of up to {IP_RATE_LIMIT_BURST}). "
    "Every answer carries them in its `X-RateLimit-*` headers. Over a limit, "
    "the answer is `429 Too Many Requests`: wait the number of seconds in "
    "`Retry-After` before trying again."
)


def build_public_openapi(
    router: APIRouter,
    *,
    title: str,
    version: str = "1.0.0",
    description: str | None = None,
) -> dict[str, Any]:
    """The OpenAPI document of `router`'s routes, and nothing else.

    It declares the X-API-Key header as the only way to authenticate, so
    Swagger UI shows an "Authorize" button and "Try it out" sends the key.

    Raises:
        ValueError: A route is not under /public/v1. Checked when the service
            starts, so an internal or frontend route can never end up in the
            public documentation by mistake.
    """
    schema: dict[str, Any] = get_openapi(
        title=title,
        version=version,
        description="\n\n".join(filter(None, [description, RATE_LIMITS_DESCRIPTION])),
        routes=router.routes,
    )

    # Checked on the generated document, not on router.routes: since FastAPI
    # 0.143, an included router stays a wrapper in router.routes, so its
    # routes aren't listed there. The document always lists every path.
    for path in schema.get("paths", {}):
        if not path.startswith(f"{PUBLIC_API_PREFIX}/"):
            raise ValueError(
                f"{path} is not a public route: the public document only "
                f"holds routes under {PUBLIC_API_PREFIX}"
            )

    # The routes verify a Bearer token (shared_auth's HTTPBearer), so FastAPI
    # documents "HTTPBearer" and marks each route with it. But a program never
    # sends that token: it sends its key, and the gateway makes the token. So
    # the document offers the key only, for every route.
    schema.setdefault("components", {})["securitySchemes"] = {
        API_KEY_SECURITY_SCHEME: {
            "type": "apiKey",
            "in": "header",
            "name": API_KEY_HEADER_NAME,
            "description": "An API key created on the API keys page of the web "
            "app. Valid 48 hours.",
        }
    }
    for operations in schema.get("paths", {}).values():
        for operation in operations.values():
            operation.pop("security", None)
    schema["security"] = [{API_KEY_SECURITY_SCHEME: []}]
    return schema


def install_public_openapi(
    app: FastAPI,
    router: APIRouter,
    *,
    service_name: str,
    title: str | None = None,
    version: str = "1.0.0",
    description: str | None = None,
) -> str:
    """Serve `router`'s public routes as GET /public/v1/openapi/<service>.json.

    The document is built here, once, when the service starts: a non-public
    route in `router` stops the service immediately (see build_public_openapi).

    Returns:
        The document's path.
    """
    schema: dict[str, Any] = build_public_openapi(
        router,
        title=title or f"Transcendence public API: {service_name}",
        version=version,
        description=description,
    )
    path: str = public_openapi_path(service_name)

    def public_openapi_document() -> JSONResponse:
        return JSONResponse(schema)

    # Not in the service's own /openapi.json: it describes the document.
    app.add_api_route(
        path, public_openapi_document, methods=["GET"], include_in_schema=False
    )
    return path
