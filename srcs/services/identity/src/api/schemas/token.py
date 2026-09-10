from enum import StrEnum

from pydantic import BaseModel


class AuthenticationScheme(StrEnum):
    BEARER = "Bearer"


class TokenResponse(BaseModel):
    access_token: str
    token_type: AuthenticationScheme = AuthenticationScheme.BEARER
