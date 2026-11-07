from pydantic import Field

from src.infrastructure.config.base import ServiceSettings


class AppSettings(ServiceSettings):
    """
    Configuration of the web application itself (FastAPI).

    Only the running service loads it; the migration container does not need
    any of these values.
    """

    PROJECT_NAME: str

    # Origins allowed to call this API from a browser (CORS).
    BACKEND_CORS_ORIGINS: list[str] = Field(default_factory=list)

    # -----------------------------------------------------------------------
    # Content Management (topic and article catalog)
    # -----------------------------------------------------------------------

    # Base URL of Content Management, e.g. http://content-management:8000
    CONTENT_MANAGEMENT_URL: str

    # -----------------------------------------------------------------------
    # Personalization (profile)
    # -----------------------------------------------------------------------

    # Base URL of Personalization, e.g. http://personalization:8000
    PERSONALIZATION_URL: str


app_settings = AppSettings()
