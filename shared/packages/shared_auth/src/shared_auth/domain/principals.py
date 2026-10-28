from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class UserPrincipal:
    account_id: UUID
    scopes: frozenset[str]
    token: str = field(repr=False)

@dataclass(frozen=True)
class ServicePrincipal:
    name: str
    scopes: frozenset[str]
    token: str = field(repr=False)

Principal = UserPrincipal | ServicePrincipal