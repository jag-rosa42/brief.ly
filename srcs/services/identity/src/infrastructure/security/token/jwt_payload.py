from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.domain.exception import InvalidTokenError
from src.infrastructure.security.token.token_type import TokenType


class JWTTokenPayload(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_alias=True,
    )
    issuer: str = Field(alias="iss")
    # RFC 7519 allows `aud` to be a single string or a list of strings.
    audience: str | list[str] = Field(alias="aud")
    token_id: str = Field(alias="jti")
    subject: str = Field(alias="sub")
    token_type: TokenType = Field(alias="type")
    issued_at: int = Field(alias="iat")
    expires_at: int = Field(alias="exp")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> JWTTokenPayload:
        try:
            return cls.model_validate(payload)
        except ValidationError as exc:
            raise InvalidTokenError() from exc
