"""Public API documentation (ADR-0009).

Every service with public routes serves one OpenAPI document holding only
those routes, and one service (Personalization) serves the Swagger UI page
that shows every document, with a selector:

    # in each service's main.py, after including its routers
    install_public_openapi(app, public_routers, service_name="morning-briefing")

    # in the one service that hosts the page
    install_public_docs_page(app, documents=[
        PublicDocument("Personalization", public_openapi_path("personalization")),
        PublicDocument("Morning Briefing", public_openapi_path("morning-briefing")),
    ])

Why not FastAPI's own /docs and /openapi.json? They describe every route of
the service: frontend, internal, health. The public documents must show only
the public API, and the gateway never routes a service's own /docs.

The gateway routes these paths without ForwardAuth, so they are readable
without a key (docs/api/02_personalization.md, "Public documentation").

One module per job:
    paths.py       the prefix, the paths and the key header
    responses.py   the errors every public route documents, and the limits
    openapi.py     one service's document
    swagger_ui.py  the pinned Swagger UI files and their hashes
    docs_page.py   the page with the selector
"""

from shared_auth.api.public_docs.docs_page import (
    PublicDocument,
    build_public_docs_html,
    build_public_docs_init_script,
    install_public_docs_page,
)
from shared_auth.api.public_docs.openapi import (
    RATE_LIMITS_DESCRIPTION,
    build_public_openapi,
    install_public_openapi,
)
from shared_auth.api.public_docs.paths import (
    API_KEY_HEADER_NAME,
    API_KEY_SECURITY_SCHEME,
    PUBLIC_API_PREFIX,
    PUBLIC_DOCS_PATH,
    public_openapi_path,
)
from shared_auth.api.public_docs.responses import (
    IP_RATE_LIMIT_BURST,
    IP_RATE_LIMIT_PER_SECOND,
    KEY_RATE_LIMIT_BURST,
    KEY_RATE_LIMIT_PER_SECOND,
    PUBLIC_API_RESPONSES,
    RATE_LIMIT_HEADERS,
    OpenApiHeader,
    OpenApiResponse,
    to_fastapi_responses,
)
from shared_auth.api.public_docs.swagger_ui import (
    SWAGGER_UI_CSS_INTEGRITY,
    SWAGGER_UI_CSS_URL,
    SWAGGER_UI_FAVICON_URL,
    SWAGGER_UI_JS_INTEGRITY,
    SWAGGER_UI_JS_URL,
    SWAGGER_UI_PRESET_INTEGRITY,
    SWAGGER_UI_PRESET_URL,
    SWAGGER_UI_VERSION,
)

__all__: list[str] = [
    "API_KEY_HEADER_NAME",
    "API_KEY_SECURITY_SCHEME",
    "IP_RATE_LIMIT_BURST",
    "IP_RATE_LIMIT_PER_SECOND",
    "KEY_RATE_LIMIT_BURST",
    "KEY_RATE_LIMIT_PER_SECOND",
    "PUBLIC_API_PREFIX",
    "PUBLIC_API_RESPONSES",
    "PUBLIC_DOCS_PATH",
    "RATE_LIMITS_DESCRIPTION",
    "RATE_LIMIT_HEADERS",
    "SWAGGER_UI_CSS_INTEGRITY",
    "SWAGGER_UI_CSS_URL",
    "SWAGGER_UI_FAVICON_URL",
    "SWAGGER_UI_JS_INTEGRITY",
    "SWAGGER_UI_JS_URL",
    "SWAGGER_UI_PRESET_INTEGRITY",
    "SWAGGER_UI_PRESET_URL",
    "SWAGGER_UI_VERSION",
    "OpenApiHeader",
    "OpenApiResponse",
    "PublicDocument",
    "build_public_docs_html",
    "build_public_docs_init_script",
    "build_public_openapi",
    "install_public_docs_page",
    "install_public_openapi",
    "public_openapi_path",
    "to_fastapi_responses",
]
