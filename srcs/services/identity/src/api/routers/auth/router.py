from fastapi import APIRouter, status

from src.api.dependencies import (
    LoginAccountDep,
    LogoutAccountDep,
    RefreshAccountSessionDep,
    RegisterAccountDep,
)
from src.api.schemas.authentication import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
)
from src.api.schemas.session import AccountSessionResponse
from src.application.use_cases.session.account_session import AccountSession

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AccountSessionResponse,
)
def register(
    body: RegisterRequest,
    register_account: RegisterAccountDep,
) -> AccountSessionResponse:
    session: AccountSession = register_account.execute(
        email=body.email, password=body.password.get_secret_value()
    )
    return AccountSessionResponse.from_session(session)


@router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=AccountSessionResponse,
)
def login(
    body: LoginRequest,
    login_account: LoginAccountDep,
) -> AccountSessionResponse:
    session: AccountSession = login_account.execute(
        email=body.email,
        password=body.password.get_secret_value(),
    )
    return AccountSessionResponse.from_session(session)


@router.post(
    path="/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    body: LogoutRequest,
    logout_account: LogoutAccountDep,
) -> None:
    logout_account.execute(body.refresh_token)


@router.post(
    path="/refresh",
    status_code=status.HTTP_200_OK,
    response_model=AccountSessionResponse,
)
def refresh(
    body: RefreshRequest,
    refresh_account_session: RefreshAccountSessionDep,
) -> AccountSessionResponse:
    session: AccountSession = refresh_account_session.execute(body.refresh_token)
    return AccountSessionResponse.from_session(session)
