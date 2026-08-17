from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash


@dataclass
class Account:
    id: UUID
    email: Email
    password_hash: PasswordHash
    created_at: datetime