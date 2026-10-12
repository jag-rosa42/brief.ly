from datetime import UTC, datetime

from src.application.port.unit_of_work import UnitOfWork
from src.application.use_cases.session.refresh_token_validator import (
    RefreshTokenValidator,
)
from src.domain.entities.refresh_token import RefreshToken
from src.domain.exception import InvalidTokenError, TokenExpiredError
from src.domain.repositories.refresh_token_repository import RefreshTokenRepository

# ----- logout flow -----
#
#         logout(refresh_token)
#                 │
#                 ▼
#     verify JWT signature
#                 │
#      ┌──────────┴──────────┐
#      │                     │
#   invalid/expired          valid
#      │                     │
#   return              find DB token
#                            │
#                   ┌────────┴────────┐
#                   │                 │
#               not found          found
#                   │                 │
#               return        already revoked?
#                                     │
#                            ┌────────┴────────┐
#                            │                 │
#                           yes               no
#                            │                 │
#                        return             revoke


class LogoutAccount:
    def __init__(
        self,
        uow: UnitOfWork,
        refresh_token_validator: RefreshTokenValidator,
        refresh_token_repository: RefreshTokenRepository,
    ) -> None:
        self._uow: UnitOfWork = uow
        self._refresh_token_validator: RefreshTokenValidator = refresh_token_validator
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository

    def execute(self, refresh_token: str) -> None:
        """Log out the account associated with a refresh token.

        Logout is intentionally idempotent. If the supplied token is
        invalid, expired, or has already been revoked, there is nothing
        left to revoke, so the operation succeeds without raising an
        exception.

        For a valid, active refresh token, the token is revoked and the
        change is persisted to the repository.

        Args:
            refresh_token: The refresh token presented by the client to be revoked.
        """
        with self._uow:
            try:
                stored: RefreshToken = (
                    self._refresh_token_validator.get_valid_refresh_token(
                        refresh_token,
                        for_update=True,
                    )
                )
            except (InvalidTokenError, TokenExpiredError):
                return

            if stored.is_revoked():
                return

            stored.revoke(datetime.now(UTC))

            # False only if the token was revoked concurrently.
            # Logout is idempotent: nothing left to do
            if self._refresh_token_repository.update(stored):
                self._uow.commit()
