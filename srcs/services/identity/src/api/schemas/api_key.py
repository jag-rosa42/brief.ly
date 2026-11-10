import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field, StringConstraints, field_validator

from src.application.use_cases.api_keys.create_api_key import CreatedApiKey
from src.domain.entities.api_key import ApiKey, ApiKeyScope

# Surrounding spaces are removed first, so "   " is refused as empty.
ApiKeyName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
]


class CreateApiKeyRequest(BaseModel):
    name: ApiKeyName
    # Only "read" and "write" are accepted (the enum), 1 or 2 of them.
    scopes: list[ApiKeyScope] = Field(min_length=1, max_length=2)

    @field_validator("scopes")
    @classmethod
    def refuse_duplicates(cls, scopes: list[ApiKeyScope]) -> list[ApiKeyScope]:
        # ["read", "read"] is most likely a client bug: refuse it rather than
        # silently storing one scope (docs/api/01_identity.md).
        if len(set(scopes)) != len(scopes):
            raise ValueError("scopes must not contain duplicates")
        return scopes


class ApiKeyResponse(BaseModel):
    """A key as the list shows it: everything except the key itself."""

    id: uuid.UUID
    name: str
    prefix: str
    scopes: list[ApiKeyScope]
    created_at: datetime
    expires_at: datetime

    @classmethod
    def from_domain(cls, api_key: ApiKey) -> Self:
        return cls(
            id=api_key.id,
            name=api_key.name,
            prefix=api_key.prefix,
            # Sorted, so the answer is the same every time.
            scopes=sorted(api_key.scopes),
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
        )


class CreatedApiKeyResponse(ApiKeyResponse):
    """The creation answer: the only time the full key is ever sent."""

    key: str

    @classmethod
    def from_created(cls, created: CreatedApiKey) -> Self:
        return cls(
            **ApiKeyResponse.from_domain(created.api_key).model_dump(),
            key=created.key,
        )
