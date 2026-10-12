from src.application.use_cases.session.account_session import AccountSession
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.domain.entities.account import Account
from src.domain.entities.refresh_token import RefreshToken
from tests.fixtures.security import FakeTokenService
from tests.fixtures.sessions import FakeRefreshTokenRepository
from tests.fixtures.unit_of_work import FakeUnitOfWork


class TestCreateAccountSession:
    def test_returns_access_and_refresh_tokens(
        self,
        create_account_session: CreateAccountSession,
        account: Account,
    ):
        session = create_account_session.execute(account.id)

        assert session.access_token == "fake-access-token-1"
        assert session.refresh_token == "fake-refresh-token-1"

    def test_access_tokens_belongs_to_the_account(
        self,
        create_account_session: CreateAccountSession,
        token_service: FakeTokenService,
        account: Account,
    ):
        session = create_account_session.execute(account.id)

        claims = token_service.verify_access_token(session.access_token)
        assert claims.account_id == account.id

    def test_persists_the_refresh_token_hash(
        self,
        create_account_session: CreateAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        token_service: FakeTokenService,
        account: Account,
    ):
        session: AccountSession = create_account_session.execute(account.id)

        stored: RefreshToken = refresh_token_repository.get(session.refresh_token_id)

        assert stored.account_id == account.id
        assert stored.token_hash == token_service.hash_token(session.refresh_token)
        assert stored.account_id != session.refresh_token
        assert stored.is_revoked() is False
        assert stored.replaced_by is None

    def test_does_not_commit(
        self,
        create_account_session: CreateAccountSession,
        uow: FakeUnitOfWork,
        account: Account,
    ):
        create_account_session.execute(account.id)

        # The caller (login / register /refresh) owns the commit transaction
        assert uow.committed is False

    def test_each_call_creates_a_distinct_session(
        self,
        create_account_session: CreateAccountSession,
        refresh_token_repository: FakeRefreshTokenRepository,
        account: Account,
    ):
        first_session = create_account_session.execute(account.id)
        second_session = create_account_session.execute(account.id)

        assert first_session.refresh_token != second_session.refresh_token
        assert first_session.refresh_token_id != second_session.refresh_token_id
        assert refresh_token_repository.count() == 2
