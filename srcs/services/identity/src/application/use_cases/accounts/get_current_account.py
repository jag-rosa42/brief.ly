from src.application.port.token.service import TokenService
from src.application.port.token.types import AccessTokenClaims
from src.domain.entities.account import Account
from src.domain.exception import InvalidTokenError
from src.domain.repositories.account_repository import AccountRepository


class GetCurrentAccount:
    """Return the account authenticated by an access token.

    The access token is checked statelessly: signature, expiry, token type,
    and the existence of its account. There is no revocation check, so an
    access token stays valid until it expires, even after a logout or after
    token theft was detected during a refresh.
    See docs/adr/0005-accept-non-revocable-access-tokens.md.
    """

    def __init__(
        self,
        account_repository: AccountRepository,
        token_service: TokenService,
    ) -> None:
        self._accounts: AccountRepository = account_repository
        self._token_service: TokenService = token_service

    def execute(self, access_token: str) -> Account:
        claims: AccessTokenClaims = self._token_service.verify_access_token(
            access_token
        )
        account: Account | None = self._accounts.find_by_id(
            claims.account_id
        )
        if account is None:
            raise InvalidTokenError()
        return account
