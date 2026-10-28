from uuid import UUID

from shared_auth.application.port.token_verifier import TokenVerifier
from shared_auth.domain.exceptions import InvalidTokenError
from shared_auth.domain.principals import ServicePrincipal, UserPrincipal
from shared_auth.domain.token_type import TokenType
from shared_auth.domain.verified_token import VerifiedToken

SERVICE_SUBJECT_PREFIX: str = "service:"


class Authenticator:
    """Turn a verified token into a principal, for one kind of caller.

    The verifier answers "is this a valid token for this service?".
    The authenticator answers "is it the right kind of token for this route?".
    A token's audience and type must match:

        caller          type      aud
        user            access    JWT_ACCESS_AUDIENCE      (transcendence:api)
        public API      access    JWT_PUBLIC_API_AUDIENCE  (transcendence:public-api)
        forwarded user  access    either of the two above
        service         service   JWT_SERVICE_AUDIENCE     (transcendence:<this service>)

    So a browser token cannot be used on the public API, a public API token
    cannot be used on a frontend route, and a service token meant for another
    service is refused.

    It receives the verifier through its port, so it knows nothing about JWTs
    or settings: api/installation.py builds both at startup.
    """

    def __init__(
        self,
        verifier: TokenVerifier,
        *,
        access_audience: str,
        service_audience: str,
        public_api_audience: str | None = None,
    ) -> None:
        self._verifier: TokenVerifier = verifier
        self._access_audience: str = access_audience
        self._service_audience: str = service_audience
        self._public_api_audience: str | None = public_api_audience
        self._forwarded_audiences: frozenset[str] = frozenset(
            audience
            for audience in (access_audience, public_api_audience)
            if audience is not None
        )

    # -----------------------------------------------------------------------
    # One method per kind of caller
    # -----------------------------------------------------------------------

    def user(self, token: str) -> UserPrincipal:
        """A logged-in user, with a browser access token (frontend routes)."""
        verified_token: VerifiedToken = self._verifier.verify(token)
        return self._as_user(
            verified_token=verified_token,
            audiences=frozenset({self._access_audience}),
        )

    def public_api_user(self, token: str) -> UserPrincipal:
        """
        A user calling the public API (the token issued by the gateway).
        Only services that serve the public API configured its audience.
        """
        if self._public_api_audience is None:
            raise RuntimeError("JWT_PUBLIC_API_AUDIENCE not configured for this service")
        verified_token: VerifiedToken = self._verifier.verify(token)
        return self._as_user(
            verified_token=verified_token,
            audiences=frozenset({self._public_api_audience}),
        )

    def forwarded_user(self, token: str) -> UserPrincipal:
        """A user's token forwarded unchanged by another service (internal routes)."""
        verified_token: VerifiedToken = self._verifier.verify(token)
        return self._as_user(
            verified_token=verified_token,
            audiences=self._forwarded_audiences,
        )

    def service(self, token: str) -> ServicePrincipal:
        """Another service, with its own service token."""
        verified_token: VerifiedToken = self._verifier.verify(token)
        return self._as_service(verified_token)

    # -----------------------------------------------------------------------
    # Principal construction and validation
    # -----------------------------------------------------------------------

    def _as_user(
        self,
        verified_token: VerifiedToken,
        audiences: frozenset[str],
    ) -> UserPrincipal:
        if (
            verified_token.token_type != TokenType.ACCESS
            or verified_token.audience not in audiences
        ):
            raise InvalidTokenError()
        try:
            account_id = UUID(verified_token.subject)
        except ValueError as exc:
            raise InvalidTokenError() from exc
        return UserPrincipal(
            account_id=account_id,
            scopes=verified_token.scopes,
            token=verified_token.raw,
        )

    def _as_service(self, verified_token: VerifiedToken) -> ServicePrincipal:
        if (
            verified_token.token_type != TokenType.SERVICE
            or verified_token.audience != self._service_audience
        ):
            raise InvalidTokenError()
        if not verified_token.subject.startswith(SERVICE_SUBJECT_PREFIX):
            raise InvalidTokenError()

        name = verified_token.subject.removeprefix(SERVICE_SUBJECT_PREFIX)
        if not name:
            raise InvalidTokenError()

        return ServicePrincipal(
            name=name,
            scopes=verified_token.scopes,
            token=verified_token.raw,
        )
