class FakeServiceTokenProvider:
    """Stands for shared_auth's ClientCredentialsTokenProvider: no Identity call.

    Gives `token`, or raises `error` when one is given (Identity down or
    refusing our credentials).
    """

    def __init__(
        self, token: str = "service-token", error: Exception | None = None
    ) -> None:
        self._token = token
        self._error = error

    def get_token(self) -> str:
        if self._error is not None:
            raise self._error
        return self._token
