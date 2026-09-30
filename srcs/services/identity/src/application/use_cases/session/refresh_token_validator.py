from src.application.port.token.service import TokenService
from src.application.port.token.types import RefreshTokenClaims
from src.domain.entities.refresh_token import RefreshToken
from src.domain.exception import InvalidTokenError
from src.domain.repositories.refresh_token_repository import RefreshTokenRepository

#             Client
#                │
#                │ refresh token
#                ▼
#    ┌─────────────────────────┐
#    │  verify_refresh_token() │
#    │                         │
#    │ signature               │
#    │ expiration              │
#    │ claims                  │
#    │ token type              │
#    └────────────┬────────────┘
#                 │
#                 │ claims.id
#                 ▼
#    ┌─────────────────────────┐
#    │ find_by_id(claims.id)   │
#    │                         │
#    │ Database                │
#    │ RefreshToken            │
#    └────────────┬────────────┘
#                 │
#                 │ stored hash
#                 ▼
#    ┌─────────────────────────┐
#    │ hash(presented token)   │
#    │         ==              │
#    │ stored_token.token_hash │
#    └────────────┬────────────┘
#                 │
#                 ▼
#           RefreshToken


class RefreshTokenValidator:
    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
    ) -> None:
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository
        self._token_service: TokenService = token_service

    def get_valid_refresh_token(self, refresh_token: str) -> RefreshToken:
        """Validate a refresh token and return its stored database entity.

        Validation happens in two stages:

        1. The token service verifies the token's cryptographic properties,
           such as its signature, claims, expiration, and token type.
        2. The repository verifies that the token corresponds to a stored
           refresh-token record by matching its ID and hash.

        The raw refresh token is never stored in the database. Only its
        hash is stored, so the presented token is hashed before comparison.

        Args:
            refresh_token: The raw refresh token presented by the client.

        Returns:
            The stored RefreshToken entity corresponding to the presented
            token.

        Raises:
            InvalidTokenError: If the token is invalid, does not correspond
                to a stored token, or its hash does not match the stored hash.
            TokenExpiredError: If the token has expired according to the
                token service.
        """
        # Verify the JWT signature, claims, token type, etc.
        claims: RefreshTokenClaims = self._token_service.verify_refresh_token(
            refresh_token
        )

        # Find the database record corresponding to the JWT's `jti`.
        stored_token: RefreshToken | None = self._refresh_token_repository.find_by_id(
            claims.id,
        )

        # The database stores only the hash of the refresh token.
        # Hash the presented token and compare it with the stored hash.
        if (
            stored_token is None
            or stored_token.token_hash != self._token_service.hash_token(refresh_token)
        ):
            raise InvalidTokenError()
        return stored_token
