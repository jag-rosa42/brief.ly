from src.application.port.password_hasher import PasswordHasher
from src.application.port.token.service import TokenService
from src.domain.entities.account import Account
from src.domain.exception import InvalidCredentialsError
from src.domain.repositories.account_repository import AccountRepository
from src.domain.value_objects.email import Email


class LoginAccount:
    def __init__(
        self,
        account_repository: AccountRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._account_repository: AccountRepository = account_repository
        self._password_hasher: PasswordHasher = password_hasher
        self._token_service: TokenService = token_service

    def execute(self, email: str, password: str) -> str:
        account: Account | None = self._account_repository.find_by_email(Email(email))
        if account is None:
            raise InvalidCredentialsError()
        if not self._password_hasher.verify(password, account.password_hash):
            raise InvalidCredentialsError()
        return self._token_service.create_access_token(account.id)
