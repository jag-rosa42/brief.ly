from datetime import UTC, datetime

from fastapi import APIRouter, status
from shared_errors import ErrorResponse

from src.api.dependencies import SynchronizeSourcesDep
from src.api.errors import IngestionFailedError
from src.api.schemas.ingestion_run import IngestionRunResponse

router = APIRouter(
    prefix="/ingestion-runs",
    tags=["ingestion-runs"],
)


@router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    response_model=IngestionRunResponse,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    },
)
def create_ingestion_run(
    synchronize_sources: SynchronizeSourcesDep,
) -> IngestionRunResponse:
    result = synchronize_sources.execute(datetime.now(UTC))
    if not result.succeeded:
        raise IngestionFailedError()

    response_status = "partial" if result.has_failures else "succeeded"
    return IngestionRunResponse(status=response_status)
