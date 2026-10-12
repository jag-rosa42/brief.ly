from typing import Annotated

from fastapi import Depends

from src.api.dependencies.database import SessionDep, UnitOfWorkDep
from src.api.dependencies.security import (
    AccessTokenDep,
    CreateAccountSessionDep,
    PasswordHasherDep,
    RefreshTokenRepositoryDep,
    RefreshTokenValidatorDep,
    TokenServiceDep,
)
from src.application.use_cases.accounts.get_current_account import GetCurrentAccount
from src.application.use_cases.auth.login_account import LoginAccount
from src.application.use_cases.auth.logout_account import LogoutAccount
from src.application.use_cases.auth.register_account import RegisterAccount
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
    uow: UnitOfWorkDep,
    account_repository: AccountRepositoryDep,
    password_hasher: PasswordHasherDep,
    create_account_session: CreateAccountSessionDep,
) -> RegisterAccount:
    return RegisterAccount(
        uow,
        account_repository,
        password_hasher,
        create_account_session,
    )


RegisterAccountDep = Annotated[RegisterAccount, Depends(get_register_account)]


# ---------------------------------------------------------------------------
# Login Account
# ---------------------------------------------------------------------------
def get_login_account(
    uow: UnitOfWorkDep,
    account_repository: AccountRepositoryDep,
    password_hasher: PasswordHasherDep,
    create_account_session: CreateAccountSessionDep,
) -> LoginAccount:
    return LoginAccount(
        uow,
        account_repository,
        password_hasher,
        create_account_session,
    )


LoginAccountDep = Annotated[LoginAccount, Depends(get_login_account)]


# ---------------------------------------------------------------------------
# Logout Account
# ---------------------------------------------------------------------------
def get_logout_account(
    uow: UnitOfWorkDep,
    refresh_token_validator: RefreshTokenValidatorDep,
    refresh_token_repository: RefreshTokenRepositoryDep,
) -> LogoutAccount:
    return LogoutAccount(
        uow,
        refresh_token_validator,
        refresh_token_repository,
    )


LogoutAccountDep = Annotated[LogoutAccount, Depends(get_logout_account)]


# ---------------------------------------------------------------------------
# Current Account
# ---------------------------------------------------------------------------


def get_current_account(
    account_repository: AccountRepositoryDep,
    token_service: TokenServiceDep,
    access_token: AccessTokenDep,
) -> Account:
    return GetCurrentAccount(account_repository, token_service).execute(
        access_token.credentials
    )


CurrentAccountDep = Annotated[Account, Depends(get_current_account)]
