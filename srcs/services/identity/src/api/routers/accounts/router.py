from fastapi import APIRouter, status
from shared_errors import ErrorResponse

from src.api.dependencies import CurrentAccountDep
from src.api.schemas.account import AccountResponse

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)


@router.get(
    path="/me",
    status_code=status.HTTP_200_OK,
    response_model=AccountResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "INVALID_TOKEN or TOKEN_EXPIRED",
        },
    },
)
def get_me(current_account: CurrentAccountDep) -> AccountResponse:
    return AccountResponse.from_domain(current_account)
