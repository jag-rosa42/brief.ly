import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class AccountRegisterRequest(BaseModel):
    email: EmailStr = Field(max_length=255)
    password: SecretStr = Field(min_length=8, max_length=255)


class AccountRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
