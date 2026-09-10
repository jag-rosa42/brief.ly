from src.application.port.token.service import TokenService
from src.application.port.token.types import AccessTokenPayload
from src.domain.entities.account import Account
from src.domain.exception import InvalidTokenError
from src.domain.repositories.account_repository import AccountRepository


class GetCurrentAccount:
    def __init__(
        self,
        account_repository: AccountRepository,
        token_service: TokenService,
    ) -> None:
        self._accounts: AccountRepository = account_repository
        self._token_service: TokenService = token_service

    def execute(self, access_token: str) -> Account:
        access_token_payload: AccessTokenPayload = (
            self._token_service.decode_access_token(access_token)
        )
        account: Account | None = self._accounts.find_by_id(
            access_token_payload.account_id
        )
        if account is None:
            raise InvalidTokenError()
        return account
