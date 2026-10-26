from enum import StrEnum


class ApiErrorCode(StrEnum):
    INGESTION_FAILED = "INGESTION_FAILED"


class ApiError(Exception):
    code: ApiErrorCode

    def __init__(self, message: str) -> None:
        super().__init__(message)


class IngestionFailedError(ApiError):
    code = ApiErrorCode.INGESTION_FAILED

    def __init__(self) -> None:
        super().__init__("Article ingestion completed with errors.")
