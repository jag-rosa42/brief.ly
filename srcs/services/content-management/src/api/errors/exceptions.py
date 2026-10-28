from enum import StrEnum


class ApiErrorCode(StrEnum):
    ARTICLE_INGESTION_FAILED = "ARTICLE_INGESTION_FAILED"


class ApiError(Exception):
    code: ApiErrorCode

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ArticleIngestionFailedError(ApiError):
    code = ApiErrorCode.ARTICLE_INGESTION_FAILED

    def __init__(self) -> None:
        super().__init__("Article ingestion completed with errors.")
