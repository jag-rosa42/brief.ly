"""The digest and its follow-up chat (ADR-0011, docs/api/05_ai-processing.md).

The browser calls /api/ai-processing/digest[/chat]; the gateway limits how
often (rate limit per session, and at most 2 answers at once for everyone,
srcs/gateway/dynamic/routers.yaml), strips /api/ai-processing, and forwards.

Both routes answer a stream of Server-Sent Events (see api/streaming.py).
Sync routes, like the rest of the service: FastAPI runs them in its thread
pool, so the profile and topic calls don't block other requests.
"""

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from shared_auth import CurrentUserDep

from src.api.dependencies import WriteDigestDep
from src.api.routers.digest.responses import DIGEST_STREAM_RESPONSES
from src.api.schemas.chat import ChatRequest
from src.api.schemas.digest import DigestRequest
from src.api.streaming import EventStream

router = APIRouter(prefix="/digest", tags=["digest"])


@router.post(
    path="",
    status_code=status.HTTP_200_OK,
    response_class=StreamingResponse,
    responses=DIGEST_STREAM_RESPONSES,
)
def write_digest(
    user: CurrentUserDep,
    request: DigestRequest,
    write_digest: WriteDigestDep,
) -> StreamingResponse:
    # The topics come from the user's token (forwarded to Personalization),
    # never from the request body.
    chunks = write_digest.digest(user.token, request.length, request.focus)
    return EventStream(chunks).response()


@router.post(
    path="/chat",
    status_code=status.HTTP_200_OK,
    response_class=StreamingResponse,
    responses=DIGEST_STREAM_RESPONSES,
)
def answer_question(
    user: CurrentUserDep,
    request: ChatRequest,
    write_digest: WriteDigestDep,
) -> StreamingResponse:
    chunks = write_digest.answer(user.token, request.to_domain())
    return EventStream(chunks).response()
