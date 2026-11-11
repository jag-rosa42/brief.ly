"""The names the public API is built on: its prefix, its paths, its key header."""

PUBLIC_API_PREFIX: str = "/public/v1"
PUBLIC_DOCS_PATH: str = f"{PUBLIC_API_PREFIX}/docs"

# The header a program sends its key in. The gateway reads it; the services
# never see it (they receive the public API token instead).
API_KEY_HEADER_NAME: str = "X-API-Key"
API_KEY_SECURITY_SCHEME: str = "ApiKey"


def public_openapi_path(service_name: str) -> str:
    """Where a service serves its public document, e.g. for "personalization":
    /public/v1/openapi/personalization.json."""
    return f"{PUBLIC_API_PREFIX}/openapi/{service_name}.json"
