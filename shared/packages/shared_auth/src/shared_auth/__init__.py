from shared_auth.api.dependencies import (
    BearerTokenDep,
    CurrentForwardedUserDep,
    CurrentServiceDep,
    CurrentUserDep,
    require_public_api_scopes,
    require_service_scopes,
)
from shared_auth.api.installation import install_authentication
from shared_auth.application.authenticator import Authenticator
from shared_auth.application.port.token_verifier import TokenVerifier
from shared_auth.domain.exceptions import (
    AuthenticationError,
    ErrorCode,
    InsufficientScopeError,
    InvalidTokenError,
    TokenExpiredError,
)
from shared_auth.domain.principals import Principal, ServicePrincipal, UserPrincipal
from shared_auth.domain.scopes import ensure_scopes
from shared_auth.domain.token_type import TokenType
from shared_auth.domain.verified_token import VerifiedToken
from shared_auth.infrastructure.clients.client_credentials_token_provider import (
    ClientCredentialsTokenProvider,
)
from shared_auth.infrastructure.clients.downstream_client import (
    DownstreamClient,
)
from shared_auth.infrastructure.clients.exceptions import DownstreamError
from shared_auth.infrastructure.settings import AuthSettings
from shared_auth.infrastructure.tokens.jwt_token_verifier import JWTTokenVerifier

__all__: list[str] = [
    "AuthSettings",
    "AuthenticationError",
    "Authenticator",
    "BearerTokenDep",
    "ClientCredentialsTokenProvider",
    "CurrentForwardedUserDep",
    "CurrentServiceDep",
    "CurrentUserDep",
    "DownstreamClient",
    "DownstreamError",
    "ErrorCode",
    "InsufficientScopeError",
    "InvalidTokenError",
    "JWTTokenVerifier",
    "Principal",
    "ServicePrincipal",
    "TokenExpiredError",
    "TokenType",
    "TokenVerifier",
    "UserPrincipal",
    "VerifiedToken",
    "ensure_scopes",
    "install_authentication",
    "require_public_api_scopes",
    "require_service_scopes",
]
