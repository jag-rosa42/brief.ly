from datetime import UTC, datetime
from uuid import UUID

from src.application.use_cases.session.account_session import AccountSession
from src.application.use_cases.session.create_account_session import CreateAccountSession
from src.application.use_cases.session.refresh_token_validator import (
    RefreshTokenValidator,
)
from src.domain.entities.refresh_token import RefreshToken
from src.domain.exception import TokenExpiredError, TokenRevokedError
from src.domain.repositories.refresh_token_repository import RefreshTokenRepository

# ----- Refresh Session Diagram Flow -----
#             CLIENT
#                │
#                │ POST /auth/refresh
#                │ refresh_token = RT₁
#                ▼
#       ┌─────────────────────┐
#       │ RefreshAccountSession│
#       │      .execute()      │
#       └──────────┬──────────┘
#                  │
#                  ▼
#   ┌─────────────────────────────┐
#   │ RefreshTokenValidator       │
#   │ get_valid_refresh_token()   │
#   └─────────────┬───────────────┘
#                 │
#                 ▼
#      Verify JWT signature
#      Verify claims / exp / type
#                 │
#           ┌─────┴─────┐
#           │           │
#        invalid       valid
#           │           │
#           ▼           ▼
#       ERROR       Find RT₁ by jti
#                       │
#                 ┌─────┴─────┐
#                 │           │
#             not found      found
#                 │           │
#                 ▼           ▼
#               ERROR    Compare hash
#                           │
#                     ┌─────┴─────┐
#                     │           │
#                  mismatch     match
#                     │           │
#                     ▼           ▼
#                   ERROR     RT₁ found
#                               │
#                               ▼
#                  _validate_refresh_token_state()
#                               │
#                    ┌──────────┴──────────┐
#                    │                     │
#                revoked               active
#                    │                     │
#                    ▼                     ▼
#            was RT₁ rotated?        check expiration
#          (replaced_by set?)              │
#                    │               ┌──────┴──────┐
#              ┌─────┴─────┐         │             │
#              │           │      expired       valid
#             yes          no        │             │
#              │           │         ▼             ▼
#              ▼           │       ERROR      continue
#      revoke ALL tokens   │                        │
#      for account (theft) │                        ▼
#              │           │           CreateAccountSession
#              ▼           │                        │
#            COMMIT        │                        ▼
#              │           │                    Create RT₂
#              │           │                    Create AT₂
#              └─────┬─────┘                        │
#                    ▼                              ▼
#                  ERROR                       Revoke RT₁
#         (logout replay: rejected,           replaced_by = RT₂
#          other sessions untouched)                │
#                                                    ▼
#                                                 COMMIT
#                                                    │
#                                                    ▼
#                                          Return AT₂ + RT₂


class RefreshAccountSession:
    def __init__(
        self,
        refresh_token_validator: RefreshTokenValidator,
        refresh_token_repository: RefreshTokenRepository,
        create_account_session: CreateAccountSession,
    ) -> None:
        self._refresh_token_validator: RefreshTokenValidator = refresh_token_validator
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository
        self._create_account_session: CreateAccountSession = create_account_session

    def execute(self, refresh_token: str) -> AccountSession:
        """Refresh an account session using a valid refresh token.

        The refresh token is rotated as part of the operation: the token
        supplied by the caller is revoked and a new refresh token is issued.

        If the supplied token was already revoked *because it was rotated*
        (i.e. it has already been exchanged once), presenting it again is
        treated as token reuse: all refresh tokens belonging to the account
        are revoked before raising TokenRevokedError, since two parties
        holding the same rotated token is a signal of compromise.

        If the supplied token was revoked by a logout instead (never
        rotated), it is simply rejected: no other session for the account
        is affected, since a stale or replayed logout is not evidence of
        theft.

        Args:
            refresh_token: The refresh token presented by the client.

        Returns:
            A new AccountSession containing a new access token and
            refresh token.

        Raises:
            InvalidTokenError: If the token is invalid or cannot be found.
            TokenExpiredError: If the stored refresh token has expired.
            TokenRevokedError: If the refresh token has already been revoked
                (whether by rotation or logout).
        """

        # 1. Verify the JWT and find the corresponding database token.
        current_refresh_token = self._refresh_token_validator.get_valid_refresh_token(
            refresh_token
        )

        now: datetime = datetime.now(UTC)

        # 2. Make sure the refresh token can still be used.
        self._validate_refresh_token_state(current_refresh_token, now)

        # 3. Create a new account session.
        new_account_session: AccountSession = self._create_account_session.execute(
            current_refresh_token.account_id
        )

        # The new refresh token must exist in the database before the old
        # token is updated to reference it through replaced_by.
        #
        # This is required because replaced_by is a foreign-key reference.
        self._refresh_token_repository.flush()

        # 4. Revoke the refresh token that was just used.
        #   - The token that was just used becomes revoked
        #   - and records the newly-created refresh token as its replacement.
        self._rotate_refresh_token(
            current_refresh_token=current_refresh_token,
            new_refresh_token_id=new_account_session.refresh_token_id,
            now=now,
        )

        # Commit INSERT + UPDATE atomically.
        # Persist the creation of the new token and the revocation of the
        # old token as one transaction.
        self._refresh_token_repository.commit()

        return new_account_session

    def _validate_refresh_token_state(
        self,
        refresh_token: RefreshToken,
        now: datetime,
    ) -> None:
        """
        Validate that a stored refresh token can still be used.

        A revoked token was consumed either by rotation (it was exchanged
        for a new one) or by logout.
        Only the rotation case is treated as reuse: presenting an
        already-rotated token again means two parties hold a copy of it,
        so every refresh token for the account is revoked
        before TokenRevokedError is raised, limiting the damage if
        the token was compromised. A token revoked by logout was never
        rotated, so replaying it is rejected without touching the
        account's other sessions.

        An expired token is rejected without changing the account's
        refresh-token state.
        """
        if refresh_token.is_revoked():
            if refresh_token.was_rotated():
                self._refresh_token_repository.revoke_all_for_account(
                    refresh_token.account_id,
                    now,
                )
            # Important: persist the security response BEFORE raising.
            #
            # The exception should not prevent the revocation from being
            # committed to the database.
                self._refresh_token_repository.commit()
            raise TokenRevokedError()

        # Check the database expiration as well.
        if refresh_token.is_expired(now):
            raise TokenExpiredError()

    def _rotate_refresh_token(
        self,
        current_refresh_token: RefreshToken,
        new_refresh_token_id: UUID,
        now: datetime,
    ) -> None:
        """Revoke the current refresh token and link it to its replacement.

        Refresh-token rotation creates a chain:

            old token -> new token -> newer token -> ...

        The old token is marked as revoked and stores the ID of the newly
        created token in ``replaced_by``.
        """
        current_refresh_token.revoke(now, replaced_by=new_refresh_token_id)

        # Persist the changed state of the old refresh token.
        self._refresh_token_repository.update(current_refresh_token)

        # The actual database commit is intentionally performed by
        # execute(), after all changes required for the rotation have
        # been prepared.
