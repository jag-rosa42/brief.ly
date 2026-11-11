"""
Public API documentation (ADR-0009): the Swagger UI page that shows every
service's document, with a selector.
"""

import json
import re
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response

from shared_auth.api.public_docs import (
    PUBLIC_DOCS_PATH,
    SWAGGER_UI_CSS_INTEGRITY,
    SWAGGER_UI_CSS_URL,
    SWAGGER_UI_JS_INTEGRITY,
    SWAGGER_UI_JS_URL,
    SWAGGER_UI_PRESET_INTEGRITY,
    SWAGGER_UI_PRESET_URL,
    SWAGGER_UI_VERSION,
    PublicDocument,
    build_public_docs_html,
    build_public_docs_init_script,
    install_public_docs_page,
    public_openapi_path,
)

DOCUMENTS: list[PublicDocument] = [
    PublicDocument("Example", public_openapi_path("example-service")),
    PublicDocument("Other", public_openapi_path("other-service")),
]


@pytest.fixture
def client() -> TestClient:
    """A service that hosts the page, and nothing else."""
    app = FastAPI()
    install_public_docs_page(app, DOCUMENTS)
    return TestClient(app)


def init_config(documents: list[PublicDocument]) -> dict[str, Any]:
    """The JSON configuration inside the page's inline script."""
    script: str = build_public_docs_init_script(documents)
    match = re.search(r"Object\.assign\((\{.*\}), \{presets", script)
    assert match is not None
    return json.loads(match.group(1))


class TestPublicDocsPage:
    def test_is_served_without_a_token(self, client: TestClient) -> None:
        response: Response = client.get(PUBLIC_DOCS_PATH)

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_loads_swagger_ui_pinned_and_checked_by_integrity(
        self, client: TestClient
    ) -> None:
        html: str = client.get(PUBLIC_DOCS_PATH).text

        for url, integrity in [
            (SWAGGER_UI_JS_URL, SWAGGER_UI_JS_INTEGRITY),
            (SWAGGER_UI_PRESET_URL, SWAGGER_UI_PRESET_INTEGRITY),
            (SWAGGER_UI_CSS_URL, SWAGGER_UI_CSS_INTEGRITY),
        ]:
            assert f'"{url}"\n  integrity="{integrity}" crossorigin="anonymous"' in html
            assert f"swagger-ui-dist@{SWAGGER_UI_VERSION}/" in url
        assert "swagger-ui-dist@5/" not in html  # FastAPI's floating default

    def test_loads_the_standalone_preset_the_selector_needs(self) -> None:
        # The selector lives in the standalone layout, which is not in
        # swagger-ui-bundle.js.
        html: str = build_public_docs_html(DOCUMENTS)

        assert SWAGGER_UI_PRESET_URL in html
        assert "SwaggerUIStandalonePreset]" in html
        assert init_config(DOCUMENTS)["layout"] == "StandaloneLayout"

    def test_lists_every_document_in_the_selector(self) -> None:
        config: dict[str, Any] = init_config(DOCUMENTS)

        assert config["urls"] == [
            {"name": "Example", "url": "/public/v1/openapi/example-service.json"},
            {"name": "Other", "url": "/public/v1/openapi/other-service.json"},
        ]
        assert config["urls.primaryName"] == "Example"

    def test_never_calls_the_online_validator_nor_keeps_the_key(self) -> None:
        config: dict[str, Any] = init_config(DOCUMENTS)

        assert config["validatorUrl"] is None
        assert config["persistAuthorization"] is False

    def test_has_one_inline_script_the_init_script(self) -> None:
        # Phase 8's Content-Security-Policy allows this script by its hash.
        html: str = build_public_docs_html(DOCUMENTS)

        inline_scripts: list[str] = re.findall(r"<script>(.*?)</script>", html, re.S)
        assert inline_scripts == [build_public_docs_init_script(DOCUMENTS)]

    def test_a_name_can_never_close_the_script(self) -> None:
        documents = [PublicDocument("</script><script>alert(1)", "/public/v1/x.json")]

        script: str = build_public_docs_init_script(documents)

        assert "</script>" not in script
        assert init_config(documents)["urls"][0]["name"] == documents[0].name

    def test_the_title_is_escaped(self) -> None:
        html: str = build_public_docs_html(DOCUMENTS, title="<b>API</b>")

        assert "<title>&lt;b&gt;API&lt;/b&gt;</title>" in html

    def test_needs_at_least_one_document(self) -> None:
        with pytest.raises(ValueError, match="at least one document"):
            build_public_docs_html([])
