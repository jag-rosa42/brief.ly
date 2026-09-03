from pydantic import BaseModel


class ErrorDetails(BaseModel):
    field: str | None = None
    message: str
    type: str | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetails] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
