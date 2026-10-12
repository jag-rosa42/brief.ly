from src.application.port.password_hasher import PasswordHasher
from src.application.port.unit_of_work import UnitOfWork
from src.application.use_cases.session.account_session import AccountSession
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.domain.entities.account import Account
from src.domain.exception import InvalidCredentialsError
from src.domain.repositories.account_repository import AccountRepository
from src.domain.value_objects.email import Email


class LoginAccount:
    def __init__(
        self,
        uow: UnitOfWork,
        account_repository: AccountRepository,
        password_hasher: PasswordHasher,
        create_account_session: CreateAccountSession,
    ) -> None:
        self._uow: UnitOfWork = uow
        self._account_repository: AccountRepository = account_repository
        self._password_hasher: PasswordHasher = password_hasher
        self._create_account_session: CreateAccountSession = create_account_session

    def execute(self, email: str, password: str) -> AccountSession:
        with self._uow:
            account: Account | None = self._account_repository.find_by_email(Email(email))
            if account is None:
                raise InvalidCredentialsError()
            if not self._password_hasher.verify(password, account.password_hash):
                raise InvalidCredentialsError()

            session: AccountSession = self._create_account_session.execute(account.id)
            self._uow.commit()

        return session
