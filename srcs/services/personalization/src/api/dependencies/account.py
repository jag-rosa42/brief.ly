from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header

from src.domain.exception import InvalidAccountIdError

# TODO(shared-auth): temporary, until shared_auth (#131) is merged. Replace this
# with its dependency, which reads the account id from the verified token's `sub`.
# This header can be forged by anyone: acceptable only while the service is not exposed.
ACCOUNT_ID_HEADER_NAME = "X-Account-Id"

AccountIdHeader = Annotated[
    str | None,
    Header(alias=ACCOUNT_ID_HEADER_NAME),
]


def get_current_account_id(account_id: AccountIdHeader = None) -> UUID:
    if account_id is None:
        raise InvalidAccountIdError()
    try:
        return UUID(account_id)
    except ValueError as error:
        raise InvalidAccountIdError() from error


CurrentAccountIdDep = Annotated[UUID, Depends(get_current_account_id)]
