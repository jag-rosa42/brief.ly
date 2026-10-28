from enum import StrEnum


class ErrorCode(StrEnum):
    ARTICLE_INGESTION_ALREADY_RUNNING = "ARTICLE_INGESTION_ALREADY_RUNNING"


class DomainError(Exception):
    code: ErrorCode

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ArticleIngestionAlreadyRunningError(DomainError):
    code = ErrorCode.ARTICLE_INGESTION_ALREADY_RUNNING

    def __init__(self) -> None:
        super().__init__("An article ingestion run is already in progress.")
