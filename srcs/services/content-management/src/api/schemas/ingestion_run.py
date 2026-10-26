from typing import Literal

from pydantic import BaseModel


class IngestionRunResponse(BaseModel):
    status: Literal["succeeded", "partial"]
