from datetime import UTC, datetime
from uuid import UUID

from src.application.port.token.service import TokenService
from src.application.port.token.types import CreatedRefreshToken
from src.application.use_cases.session.account_session import AccountSession
from src.domain.entities.refresh_token import RefreshToken
from src.domain.repositories.refresh_token_repository import RefreshTokenRepository


class CreateAccountSession:
    """Issue an access token and stage a new refresh token.

    This use case does NOT commit. It is always called from inside another
    use case's ``with uow:`` block (login, register, refresh), and that
    caller commits the new refresh token together with its own changes.
    """
    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
    ) -> None:
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository
        self._token_service: TokenService = token_service

    def execute(self, account_id: UUID) -> AccountSession:
        access_token: str = self._token_service.create_access_token(account_id)
        created_refresh_token: CreatedRefreshToken = (
            self._token_service.create_refresh_token(account_id)
        )
        refresh_token = RefreshToken(
            id=created_refresh_token.id,
            account_id=account_id,
            token_hash=created_refresh_token.token_hash,
            expires_at=created_refresh_token.expires_at,
            created_at=datetime.now(UTC),
        )

        self._refresh_token_repository.add(refresh_token)

        return AccountSession(
            access_token=access_token,
            refresh_token=created_refresh_token.token,
            refresh_token_id=created_refresh_token.id,
        )
