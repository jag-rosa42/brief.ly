from datetime import UTC, datetime

from fastapi import APIRouter, status
from shared_errors import ErrorResponse

from src.api.dependencies import SynchronizeSourcesDep
from src.api.errors import ArticleIngestionFailedError
from src.api.schemas.ingestion_run import IngestionRunResponse, IngestionRunStatus
from src.domain.exception import ArticleIngestionAlreadyRunningError
from src.infrastructure.metrics.ingestion import record_ingestion_run

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
    try:
        result = synchronize_sources.execute(datetime.now(UTC))
    except ArticleIngestionAlreadyRunningError:
        raise
    except Exception:
        record_ingestion_run("failed")
        raise

    if not result.succeeded:
        record_ingestion_run(
            "failed",
            articles_created=result.articles_created,
            failures=result.failures,
        )
        raise ArticleIngestionFailedError()

    response_status = (
        IngestionRunStatus.PARTIAL
        if result.has_failures
        else IngestionRunStatus.SUCCEEDED
    )
    record_ingestion_run(
        response_status.value,
        articles_created=result.articles_created,
        failures=result.failures,
    )
    return IngestionRunResponse(status=response_status)
