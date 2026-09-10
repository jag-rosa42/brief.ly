from typing import Annotated

from fastapi import Depends

from src.api.dependencies.database import SessionDep
from src.api.dependencies.security import (
    AccessTokenDep,
    PasswordHasherDep,
    TokenServiceDep,
)
from src.application.use_cases.get_current_account import GetCurrentAccount
from src.application.use_cases.login_account import LoginAccount
from src.application.use_cases.register_account import RegisterAccount
from src.domain.entities.account import Account
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


# ---------------------------------------------------------------------------
# Login Account
# ---------------------------------------------------------------------------
def get_login_account(
    account_repository: AccountRepositoryDep,
    password_hasher: PasswordHasherDep,
    token_service: TokenServiceDep,
) -> LoginAccount:
    return LoginAccount(account_repository, password_hasher, token_service)


LoginAccountDep = Annotated[LoginAccount, Depends(get_login_account)]


# ---------------------------------------------------------------------------
# Current Account
# ---------------------------------------------------------------------------


def get_current_account(
    account_repository: AccountRepositoryDep,
    token_service: TokenServiceDep,
    access_token: AccessTokenDep,
) -> Account:
    return GetCurrentAccount(account_repository, token_service).execute(access_token)


CurrentAccountDep = Annotated[Account, Depends(get_current_account)]
