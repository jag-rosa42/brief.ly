import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, EmailStr

from src.domain.entities.account import Account


class AccountResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime

    @classmethod
    def from_domain(cls, account: Account) -> Self:
        return cls(
            id=account.id,
            email=account.email.value,
            created_at=account.created_at,
        )
