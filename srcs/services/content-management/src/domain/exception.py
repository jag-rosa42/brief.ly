from enum import StrEnum


class ErrorCode(StrEnum):
    INGESTION_ALREADY_RUNNING = "INGESTION_ALREADY_RUNNING"


class DomainError(Exception):
    code: ErrorCode

    def __init__(self, message: str) -> None:
        super().__init__(message)


class IngestionAlreadyRunningError(DomainError):
    code = ErrorCode.INGESTION_ALREADY_RUNNING

    def __init__(self) -> None:
        super().__init__("An article ingestion run is already in progress.")
