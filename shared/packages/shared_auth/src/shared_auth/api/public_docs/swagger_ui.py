"""The Swagger UI files the docs page loads: one pinned version, with hashes.

The files come from the jsDelivr CDN. Each one has its Subresource Integrity
hash: the browser refuses the file if its content doesn't match, so a
compromised CDN can't run its own script on our page.

Upgrading means changing the version AND every hash, together:
    curl -s <url> | openssl dgst -sha384 -binary | openssl base64 -A
"""

SWAGGER_UI_VERSION: str = "5.34.0"
_SWAGGER_UI_CDN: str = (
    f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_UI_VERSION}"
)

SWAGGER_UI_JS_URL: str = f"{_SWAGGER_UI_CDN}/swagger-ui-bundle.js"
SWAGGER_UI_JS_INTEGRITY: str = (
    "sha384-9Td7MKiIr2S83E1kZyyVi8KdJw/S8CpAvu0llLyMeg0xq/hDGiZJfVn0fV4llCmK"
)

# The standalone preset holds the top bar with the document selector. It is
# not in swagger-ui-bundle.js, which is why the page doesn't use FastAPI's
# get_swagger_ui_html: that page loads the bundle only.
SWAGGER_UI_PRESET_URL: str = f"{_SWAGGER_UI_CDN}/swagger-ui-standalone-preset.js"
SWAGGER_UI_PRESET_INTEGRITY: str = (
    "sha384-My2aDM4r2Mbm3ybHcubKm9O9U8FEjvF/O5nGvE9YK5dzqOTbWEKa79RPJ1krdMaF"
)

SWAGGER_UI_CSS_URL: str = f"{_SWAGGER_UI_CDN}/swagger-ui.css"
SWAGGER_UI_CSS_INTEGRITY: str = (
    "sha384-4c3vsE5f+trhFyHrFrLM1fFGUn531NIaC7dcqEWIJdoRQJ5CkJbSuSCwXLpaS1KF"
)

# From the same package: the page needs one outside host only.
SWAGGER_UI_FAVICON_URL: str = f"{_SWAGGER_UI_CDN}/favicon-32x32.png"
