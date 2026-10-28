from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    """
    What a service needs to verify tokens.

    The package cannot know where each service keeps its .env and secrets, so
    the service passes them when it creates the settings:

        auth_settings = AuthSettings(
            _env_file=BASE_DIR / ".env",
            _secrets_dir=SECRETS_DIR,
        )

    The public key comes from the `jwt_public_key` secret (a file in the
    secrets directory). A service never receives the private key.

    A service that only calls others and serves no route (AI Processing) does
    not need these settings: it only uses the clients.
    """

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Identity's public key: verifies signatures, cannot create them.
    JWT_PUBLIC_KEY: str

    # Must match Identity's settings (ADR-0007).
    JWT_ISSUER: str = "transcendence:identity"
    JWT_ACCESS_AUDIENCE: str = "transcendence:api"

    # This service's own audience, for service tokens addressed to it,
    # e.g. "transcendence:personalization". Required: there is no safe default.
    JWT_SERVICE_AUDIENCE: str

    # Only set in services that serve public routes or receive forwarded
    # public API tokens (Personalization, Morning Briefing; ADR-0009),
    # e.g. "transcendence:public-api". Leave unset elsewhere.
    JWT_PUBLIC_API_AUDIENCE: str | None = None

    @property
    def accepted_audiences(self) -> frozenset[str]:
        audiences: set[str] = {self.JWT_ACCESS_AUDIENCE, self.JWT_SERVICE_AUDIENCE}
        if self.JWT_PUBLIC_API_AUDIENCE:
            audiences.add(self.JWT_PUBLIC_API_AUDIENCE)
        return frozenset(audiences)
