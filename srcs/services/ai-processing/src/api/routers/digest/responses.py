"""What the docs show for the digest routes (docs/api/05_ai-processing.md).

Typed OpenApiResponse objects rather than a hand-written dictionary: a
missing description or a misspelled field fails when the module is loaded.
FastAPI's `responses=` takes plain dictionaries only, so to_fastapi_responses
builds one at the end.
"""

from typing import Any

from fastapi import status
from shared_auth.api.public_docs import OpenApiResponse, to_fastapi_responses
from shared_errors import ErrorResponse

from src.api.streaming import MEDIA_TYPE

DIGEST_STREAM_RESPONSES: dict[int | str, dict[str, Any]] = to_fastapi_responses(
    {
        status.HTTP_200_OK: OpenApiResponse(
            description=(
                'A text/event-stream: `chunk` events ({"text": str}), then '
                '`done` ({}) or `error` ({"error": {"code", "message"}}).'
            ),
            media_type=MEDIA_TYPE,
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="INVALID_TOKEN, TOKEN_EXPIRED (also passed through "
            "from Personalization)",
            model=ErrorResponse,
        ),
        status.HTTP_422_UNPROCESSABLE_CONTENT: OpenApiResponse(
            description="VALIDATION_ERROR (length, focus, conversation shape)",
            model=ErrorResponse,
        ),
        status.HTTP_502_BAD_GATEWAY: OpenApiResponse(
            description="DOWNSTREAM_ERROR (Personalization answered an unexpected error)",
            model=ErrorResponse,
        ),
        status.HTTP_503_SERVICE_UNAVAILABLE: OpenApiResponse(
            description="SERVICE_UNAVAILABLE (Personalization or Content "
            "Management unreachable)",
            model=ErrorResponse,
        ),
    }
)
