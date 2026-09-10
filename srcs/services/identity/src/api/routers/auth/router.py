from fastapi import APIRouter, status

from src.api.dependencies import RegisterAccountDep
from src.api.schemas.account import AccountRegisterRequest, AccountRegisterResponse
from src.domain.entities.account import Account

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AccountRegisterResponse,
)
def register(
    body: AccountRegisterRequest,
    register_account: RegisterAccountDep,
) -> AccountRegisterResponse:
    account: Account = register_account.execute(
        email=body.email, password=body.password.get_secret_value()
    )
    return AccountRegisterResponse(
        id=account.id,
        email=account.email.value,
    )
