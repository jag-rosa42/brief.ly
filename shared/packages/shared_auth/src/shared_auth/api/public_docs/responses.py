"""The errors every public route documents (ADR-0009).

Use PUBLIC_API_RESPONSES on the router that holds a service's public routes:

    public_routers = APIRouter(prefix="/public/v1", responses=PUBLIC_API_RESPONSES)
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel
from shared_errors import ErrorResponse

# ---------------------------------------------------------------------------
# Rate limits
# ---------------------------------------------------------------------------
# Copied from the gateway, which enforces them: keep both in sync.
#   srcs/gateway/dynamic/routers.yaml: public-rate-limit-key,
#   public-rate-limit-ip and public-rate-limit-info.
KEY_RATE_LIMIT_PER_SECOND: int = 5
KEY_RATE_LIMIT_BURST: int = 10
IP_RATE_LIMIT_PER_SECOND: int = 20
IP_RATE_LIMIT_BURST: int = 40


@dataclass(frozen=True)
class OpenApiHeader:
    """One header of a documented answer, e.g. Retry-After on a 429."""

    name: str
    description: str
    schema_type: str = "string"  # an OpenAPI type: "string", "integer"...


@dataclass(frozen=True)
class OpenApiResponse:
    """What the docs show for one status code of a route.

    A dataclass rather than a plain dictionary: a missing description or a
    misspelled field is an error when the module is loaded (and for ty), not
    a silently wrong page. FastAPI's `responses=` takes plain dictionaries
    only (a TypedDict is refused by the type checker), so to_fastapi() makes
    one.
    """

    description: str
    # The body's schema. None when the answer is not in our error format,
    # like Traefik's plain-text 429.
    model: type[BaseModel] | None = None
    headers: tuple[OpenApiHeader, ...] = ()

    def to_fastapi(self) -> dict[str, Any]:
        """The dictionary FastAPI's `responses=` expects for one status."""
        response: dict[str, Any] = {"description": self.description}
        if self.model is not None:
            response["model"] = self.model
        if self.headers:
            response["headers"] = {
                header.name: {
                    "description": header.description,
                    "schema": {"type": header.schema_type},
                }
                for header in self.headers
            }
        return response


def to_fastapi_responses(
    responses: Mapping[int, OpenApiResponse],
) -> dict[int | str, dict[str, Any]]:
    """Several documented answers, in the shape of FastAPI's `responses=`."""
    return {status: response.to_fastapi() for status, response in responses.items()}


# Sent on every public answer by the gateway (public-rate-limit-info).
RATE_LIMIT_HEADERS: tuple[OpenApiHeader, ...] = (
    OpenApiHeader(
        "X-RateLimit-Limit-Per-Key",
        "Requests per second allowed for one API key",
        "integer",
    ),
    OpenApiHeader(
        "X-RateLimit-Burst-Per-Key",
        "Requests one API key may send at once",
        "integer",
    ),
    OpenApiHeader(
        "X-RateLimit-Limit-Per-IP",
        "Requests per second allowed from one IP address",
        "integer",
    ),
    OpenApiHeader(
        "X-RateLimit-Burst-Per-IP",
        "Requests one IP address may send at once",
        "integer",
    ),
)

PUBLIC_API_RESPONSES: dict[int | str, dict[str, Any]] = to_fastapi_responses(
    {
        401: OpenApiResponse(
            description="Missing, unknown, revoked or expired API key "
            "(INVALID_API_KEY, answered by the gateway)",
            model=ErrorResponse,
        ),
        403: OpenApiResponse(
            description="The key lacks the scope this route needs (INSUFFICIENT_SCOPE)",
            model=ErrorResponse,
        ),
        429: OpenApiResponse(
            description=(
                "Too many requests, answered by the gateway in plain text. Limits: "
                f"{KEY_RATE_LIMIT_PER_SECOND} requests per second per API key "
                f"(bursts of {KEY_RATE_LIMIT_BURST}), "
                f"{IP_RATE_LIMIT_PER_SECOND} per second per IP address "
                f"(bursts of {IP_RATE_LIMIT_BURST}). Wait Retry-After seconds."
            ),
            headers=(
                OpenApiHeader(
                    "Retry-After", "Seconds to wait before trying again", "integer"
                ),
                *RATE_LIMIT_HEADERS,
            ),
        ),
    }
)
