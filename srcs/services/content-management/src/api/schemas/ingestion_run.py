from enum import StrEnum

from pydantic import BaseModel


class IngestionRunStatus(StrEnum):
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"


class IngestionRunResponse(BaseModel):
    status: IngestionRunStatus
