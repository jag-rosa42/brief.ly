from fastapi import APIRouter, status

from src.api.dependencies import LoginAccountDep, RegisterAccountDep
from src.api.schemas.account import AccountRegisterResponse
from src.api.schemas.authentication import LoginRequest, RegisterRequest
from src.api.schemas.token import TokenResponse
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
    body: RegisterRequest, register_account: RegisterAccountDep
) -> AccountRegisterResponse:
    account: Account = register_account.execute(
        email=body.email, password=body.password.get_secret_value()
    )
    return AccountRegisterResponse.from_domain(account)


@router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
)
def login(
    body: LoginRequest,
    login_account: LoginAccountDep,
) -> TokenResponse:
    access_token = login_account.execute(
        email=body.email, password=body.password.get_secret_value()
    )
    return TokenResponse(access_token=access_token)
