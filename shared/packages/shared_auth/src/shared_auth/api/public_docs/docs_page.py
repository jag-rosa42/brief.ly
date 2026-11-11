"""The Swagger UI page that shows every service's public document."""

import html
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from shared_auth.api.public_docs.paths import PUBLIC_DOCS_PATH
from shared_auth.api.public_docs.swagger_ui import (
    SWAGGER_UI_CSS_INTEGRITY,
    SWAGGER_UI_CSS_URL,
    SWAGGER_UI_FAVICON_URL,
    SWAGGER_UI_JS_INTEGRITY,
    SWAGGER_UI_JS_URL,
    SWAGGER_UI_PRESET_INTEGRITY,
    SWAGGER_UI_PRESET_URL,
)


@dataclass(frozen=True)
class PublicDocument:
    """One entry of the docs page's selector."""

    name: str  # shown in the selector, e.g. "Personalization"
    url: str  # e.g. public_openapi_path("personalization")


_DOCS_PAGE_TEMPLATE: str = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{css_url}"
  integrity="{css_integrity}" crossorigin="anonymous">
<link rel="icon" type="image/png" href="{favicon_url}">
</head>
<body>
<div id="swagger-ui"></div>
<script src="{js_url}"
  integrity="{js_integrity}" crossorigin="anonymous"></script>
<script src="{preset_url}"
  integrity="{preset_integrity}" crossorigin="anonymous"></script>
<script>{init_script}</script>
</body>
</html>
"""


def build_public_docs_init_script(documents: Sequence[PublicDocument]) -> str:
    """The page's only inline script: it starts Swagger UI.

    Kept apart because a Content-Security-Policy that allows it by hash
    (Phase 8) needs its exact text.

    Raises:
        ValueError: `documents` is empty.
    """
    if not documents:
        raise ValueError("The public docs page needs at least one document")

    config: dict[str, Any] = {
        "dom_id": "#swagger-ui",
        # The selector: one entry per document, in the top bar of the
        # standalone layout.
        "urls": [{"name": doc.name, "url": doc.url} for doc in documents],
        "urls.primaryName": documents[0].name,
        "layout": "StandaloneLayout",
        "deepLinking": True,
        # No call to swagger.io's online validator: the page only talks to
        # our own origin (and loads its files from the CDN).
        "validatorUrl": None,
        # Never keep the key in the browser's storage after the page is
        # closed: it is a credential.
        "persistAuthorization": False,
    }
    # json.dumps writes valid JavaScript. "<" is escaped so no value can ever
    # close the <script> element ("</script>").
    config_js: str = json.dumps(config).replace("<", "\\u003c")
    return (
        f"window.ui = SwaggerUIBundle(Object.assign({config_js}, "
        "{presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset]}));"
    )


def build_public_docs_html(
    documents: Sequence[PublicDocument],
    *,
    title: str = "Transcendence public API",
) -> str:
    """The Swagger UI page, with a selector over `documents`.

    Raises:
        ValueError: `documents` is empty.
    """
    return _DOCS_PAGE_TEMPLATE.format(
        title=html.escape(title),
        css_url=SWAGGER_UI_CSS_URL,
        css_integrity=SWAGGER_UI_CSS_INTEGRITY,
        favicon_url=SWAGGER_UI_FAVICON_URL,
        js_url=SWAGGER_UI_JS_URL,
        js_integrity=SWAGGER_UI_JS_INTEGRITY,
        preset_url=SWAGGER_UI_PRESET_URL,
        preset_integrity=SWAGGER_UI_PRESET_INTEGRITY,
        init_script=build_public_docs_init_script(documents),
    )


def install_public_docs_page(
    app: FastAPI,
    documents: Sequence[PublicDocument],
    *,
    title: str = "Transcendence public API",
) -> str:
    """Serve the Swagger UI page at GET /public/v1/docs.

    Only one service hosts it (Personalization today, ADR-0009). The page is
    built once, at startup: it is the same for every visitor.

    Returns:
        The page's path.
    """
    page: str = build_public_docs_html(documents, title=title)

    def public_docs_page() -> HTMLResponse:
        return HTMLResponse(page)

    app.add_api_route(
        PUBLIC_DOCS_PATH, public_docs_page, methods=["GET"], include_in_schema=False
    )
    return PUBLIC_DOCS_PATH
