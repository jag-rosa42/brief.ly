from enum import StrEnum

from pydantic import BaseModel

from src.application.use_cases.session.account_session import AccountSession


class AuthenticationScheme(StrEnum):
    BEARER = "Bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: AuthenticationScheme = AuthenticationScheme.BEARER

    @classmethod
    def from_session(cls, session: AccountSession) -> AccessTokenResponse:
        # session.refresh_token is sent as an HttpOnly cookie by the router
        # session.refresh_token_id is internal (rotation bookkeeping only)
        # it should deliberately never leaves the application layer.
        return cls(access_token=session.access_token)
