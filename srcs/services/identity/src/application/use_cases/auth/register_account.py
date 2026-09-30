import datetime
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from src.application.port.password_hasher import PasswordHasher
from src.application.use_cases.session.account_session import AccountSession
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.domain.entities.account import Account
from src.domain.exception import EmailAlreadyRegisteredError
from src.domain.repositories.account_repository import AccountRepository
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash


class RegisterAccount:
    def __init__(
        self,
        account_repository: AccountRepository,
        password_hasher: PasswordHasher,
        create_account_session: CreateAccountSession,
    ) -> None:
        self._account_repository: AccountRepository = account_repository
        self._password_hasher: PasswordHasher = password_hasher
        self._create_account_session: CreateAccountSession = create_account_session

    def execute(self, email: str, password: str) -> AccountSession:
        email_value_object: Email = Email(email)

        existing_account: Account | None = self._account_repository.find_by_email(
            email_value_object
        )

        if existing_account is not None:
            raise EmailAlreadyRegisteredError()

        password_hash: PasswordHash = self._password_hasher.hash(password)

        account: Account = Account(
            id=uuid4(),
            email=email_value_object,
            password_hash=password_hash,
            created_at=datetime.datetime.now(datetime.UTC),
        )
        # TODO: Revisit the transaction boundary.
        # Currently, this use case explicitly commits/rolls back through the repository.
        # Consider moving transaction management to a Unit of Work or outer application
        # boundary so the entire use case is executed within a single transaction.
        try:
            self._account_repository.save(account)
            session: AccountSession = self._create_account_session.execute(account.id)
            self._account_repository.commit()
        except IntegrityError as exc:
            self._account_repository.rollback()
            raise EmailAlreadyRegisteredError() from exc
        except Exception:
            self._account_repository.rollback()
            raise

        return session
