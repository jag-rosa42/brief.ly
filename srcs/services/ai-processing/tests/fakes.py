class FakeTokenProvider:
    """Stands in for shared_auth's ClientCredentialsTokenProvider: gives a
    fixed token, or raises `error` to simulate Identity failing."""

    def __init__(self, token: str = "service-token", error: Exception | None = None):
        self.token = token
        self.error = error

    def get_token(self) -> str:
        if self.error is not None:
            raise self.error
        return self.token
