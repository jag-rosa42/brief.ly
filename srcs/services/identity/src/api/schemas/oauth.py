from dataclasses import dataclass

from pydantic import BaseModel

from src.api.schemas.session import AuthenticationScheme
from src.application.port.token.types import CreatedServiceToken


@dataclass(frozen=True)
class ClientCredentials:
    """The ID and secret a client sends in its Basic Authorization header."""

    client_id: str
    client_secret: str


class ServiceTokenResponse(BaseModel):
    """The successful token response of RFC 6749 §5.1.

    shared_auth's ClientCredentialsTokenProvider reads exactly these three
    fields, and refuses the response if one is missing or wrong.
    """

    access_token: str
    token_type: AuthenticationScheme = AuthenticationScheme.BEARER
    expires_in: int  # seconds

    @classmethod
    def from_service_token(
        cls, service_token: CreatedServiceToken
    ) -> ServiceTokenResponse:
        return cls(access_token=service_token.token, expires_in=service_token.expires_in)
