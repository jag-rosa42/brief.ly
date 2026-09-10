from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.dependencies import SessionDep
from src.api.schemas.account import AccountRegisterRequest, AccountRegisterResponse
from src.application.use_cases.register_account import RegisterAccount
from src.domain.entities.account import Account
from src.infrastructure.database.repositories.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)
from src.infrastructure.security.password_hasher import PwdlibPasswordHasher

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


def get_register_account(
    session: SessionDep,
) -> RegisterAccount:
    account_repository: SqlAlchemyAccountRepository = SqlAlchemyAccountRepository(session)
    password_hasher: PwdlibPasswordHasher = PwdlibPasswordHasher()
    return RegisterAccount(
        account_repository,
        password_hasher,
    )


RegisterAccountDep = Annotated[
    RegisterAccount,
    Depends(get_register_account)
]


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AccountRegisterResponse,
)
def register(
    body: AccountRegisterRequest,
    register_account: RegisterAccountDep
) -> AccountRegisterResponse:
    account: Account = register_account.execute(
        email=body.email, password=body.password.get_secret_value()
    )
    return AccountRegisterResponse(
        id=account.id,
        email=account.email.value,
    )
