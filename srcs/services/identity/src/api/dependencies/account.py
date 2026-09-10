from typing import Annotated

from fastapi import Depends

from src.api.dependencies.database import SessionDep
from src.api.dependencies.security import PasswordHasherDep
from src.application.use_cases.register_account import RegisterAccount
from src.domain.repositories.account_repository import AccountRepository
from src.infrastructure.database.repositories.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)


# ---------------------------------------------------------------------------
# Account Repository
# ---------------------------------------------------------------------------
def get_account_repository(session: SessionDep) -> AccountRepository:
    return SqlAlchemyAccountRepository(session)


AccountRepositoryDep = Annotated[
    AccountRepository,
    Depends(get_account_repository),
]


# ---------------------------------------------------------------------------
# Register Account
# ---------------------------------------------------------------------------
def get_register_account(
    account_repository: AccountRepositoryDep,
    password_hasher: PasswordHasherDep,
) -> RegisterAccount:
    return RegisterAccount(account_repository, password_hasher)


RegisterAccountDep = Annotated[RegisterAccount, Depends(get_register_account)]
