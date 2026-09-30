from enum import StrEnum

from pydantic import BaseModel

from src.application.use_cases.session.account_session import AccountSession


class AuthenticationScheme(StrEnum):
    BEARER = "Bearer"


class AccountSessionResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: AuthenticationScheme = AuthenticationScheme.BEARER

    @classmethod
    def from_session(cls, session: AccountSession) -> AccountSessionResponse:
        # session.refresh_token_id is internal (rotation bookkeeping only)
        # it should deliberately never leaves the application layer.
        return cls(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
        )
