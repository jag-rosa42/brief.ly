from fastapi import APIRouter, status

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
)
def get_me(current_account: CurrentAccountDep) -> AccountResponse:
    return AccountResponse.from_domain(current_account)
