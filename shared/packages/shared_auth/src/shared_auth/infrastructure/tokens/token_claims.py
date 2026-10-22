from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from shared_auth.domain.exceptions import InvalidTokenError
from shared_auth.domain.token_type import TokenType


class TokenClaims(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_alias=True,
    )

    issuer: str = Field(alias="iss")
    # RFC 7519 allows `aud` to be a single string or a list of strings. We only
    # accept a single string: each token is meant for exactly one audience.
    audience: str = Field(alias="aud")
    subject: str = Field(alias="sub")
    token_id: str = Field(alias="jti")
    token_type: TokenType = Field(alias="type")
    issued_at: int = Field(alias="iat")
    expires_at: int = Field(alias="exp")
    # OAuth style: space-separated, e.g. "read write"
    # RFC 6749 - section 3.3
    scope: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TokenClaims:
        try:
            return cls.model_validate(payload)
        except ValidationError as exc:
            raise InvalidTokenError() from exc
