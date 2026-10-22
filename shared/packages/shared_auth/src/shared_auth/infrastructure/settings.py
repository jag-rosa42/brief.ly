from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    JWT_PUBLIC_KEY: str

    JWT_ISSUER: str = "transcendence:identity"
    JWT_ACCESS_AUDIENCE: str = "transcendence:api"

    JWT_SERVICE_AUDIENCE: str

    JWT_PUBLIC_API_AUDIENCE: str | None = None
