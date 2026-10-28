from shared_auth.domain.exceptions import ErrorCode


class DownstreamError(Exception):
    """Another service answered with an error we cannot hand back as is.

    Raised by DownstreamClient and ClientCredentialsTokenProvider (through
    raise_for_downstream_error). Adapters may catch it (for example to turn a
    downstream 404 into "not found"); otherwise the service answers 502.
    """

    code = ErrorCode.DOWNSTREAM_ERROR

    def __init__(self, service: str, status_code: int, code: str | None) -> None:
        super().__init__(f"{service} answered {status_code} ({code or 'no error code'})")
        self.service: str = service
        self.status_code: int = status_code
        self.downstream_code: str | None = code
