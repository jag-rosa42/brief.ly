from pydantic import SecretStr

from src.infrastructure.config.base import ServiceSettings


class NewsApiSettings(ServiceSettings):
    NEWS_API_KEY: SecretStr
