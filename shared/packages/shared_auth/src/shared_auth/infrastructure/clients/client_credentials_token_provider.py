"""Service tokens with OAuth 2.0 client credentials (ADR-0008).

When a service calls another one for data that belongs to no user,
it asks Identity for a short-lived token:

    POST http://identity:8000/internal/v1/oauth/token
    Authorization: Basic base64(client_id:client_secret)
    Content-Type: application/x-www-form-urlencoded

    grant_type=client_credentials&audience=transcendence:content-management&scope=summaries:write

    200 {"access_token": "...", "token_type": "Bearer", "expires_in": 300}

The token is cached and reused until shortly before it expires, so Identity
is called about once per token lifetime, not once per request.

Standards:
    - RFC 6749 §4.4, the client credentials grant (request §4.4.2, response §4.4.3)
      https://datatracker.ietf.org/doc/html/rfc6749#section-4.4
    - RFC 6749 §2.3.1, client authentication with a password (HTTP Basic)
      https://datatracker.ietf.org/doc/html/rfc6749#section-2.3.1
    - RFC 7617, the HTTP Basic scheme
      https://datatracker.ietf.org/doc/html/rfc7617
    - RFC 6749 §3.3, the scope format (space-separated list)
      https://datatracker.ietf.org/doc/html/rfc6749#section-3.3
    - RFC 6749 §5.1, the successful token response
      https://datatracker.ietf.org/doc/html/rfc6749#section-5.1
    - RFC 8707, resource indicators: the standard `resource` parameter that our
      `audience` parameter stands for (`audience` is an Auth0-style extension)
      https://datatracker.ietf.org/doc/html/rfc8707
    - RFC 6750, sending the token as `Authorization: Bearer` (DownstreamClient)
      https://datatracker.ietf.org/doc/html/rfc6750
    - RFC 9068, the JWT profile for access tokens (what Identity issues)
      https://datatracker.ietf.org/doc/html/rfc9068
    - RFC 9700, OAuth 2.0 security best current practice
      https://datatracker.ietf.org/doc/html/rfc9700

Similar implementations (permalinks, so line numbers stay correct):
    - Authlib, OAuth2Client.fetch_token() and ensure_active_token()
      https://github.com/authlib/authlib/blob/72db57bdfa45fb8ae8d38bca7377068fa7438b78/authlib/oauth2/client.py#L207-L338
    - google-auth, REFRESH_THRESHOLD (renew before expiry)
      https://github.com/googleapis/google-cloud-python/blob/ca24f265c80eb95c4a005d5497a491cb4425d236/packages/google-auth/google/auth/_helpers.py#L42
    - google-auth, service account credentials (a service gets a token for itself)
      https://github.com/googleapis/google-cloud-python/blob/ca24f265c80eb95c4a005d5497a491cb4425d236/packages/google-auth/google/oauth2/service_account.py
    - Azure SDK, ClientSecretCredential and its cache (get_token())
      https://github.com/Azure/azure-sdk-for-python/blob/8d4d2eadaec24416cd0cee94fca8cc957cf829cc/sdk/identity/azure-identity/azure/identity/_credentials/client_secret.py
      https://github.com/Azure/azure-sdk-for-python/blob/8d4d2eadaec24416cd0cee94fca8cc957cf829cc/sdk/identity/azure-identity/azure/identity/_internal/client_credential_base.py#L22
      https://github.com/Azure/azure-sdk-for-python/blob/8d4d2eadaec24416cd0cee94fca8cc957cf829cc/sdk/identity/azure-identity/azure/identity/_internal/get_token_mixin.py#L48-L156
    - Spring Security, ClientCredentialsOAuth2AuthorizedClientProvider (clockSkew)
      https://github.com/spring-projects/spring-security/blob/7f5e6398bd7b93accd79afc7bd50a1429db02fb8/oauth2/oauth2-client/src/main/java/org/springframework/security/oauth2/client/ClientCredentialsOAuth2AuthorizedClientProvider.java#L44-L103
"""

import logging
import threading
import time
from collections.abc import Callable, Iterable
from typing import ClassVar

import httpx2
from pydantic import (
    BaseModel,
    Field,
    PositiveInt,
    SecretStr,
    ValidationError,
    field_validator,
)
from shared_errors.exceptions import InfrastructureError

from shared_auth.infrastructure.clients.downstream_client import (
    DEFAULT_TIMEOUT_SECONDS,
    raise_for_downstream_error,
)

logger: logging.Logger = logging.getLogger(__name__)


class _TokenResponse(BaseModel):
    """The fields we read from a successful token response (RFC 6749 §5.1).

    A response that breaks one of these rules is refused here, as a malformed
    response (503), instead of failing later in a less obvious way:

    - access_token not empty: otherwise "Bearer " would be sent downstream,
      and the callee would answer an INVALID_TOKEN hard to trace back here.
    - token_type is "Bearer": the only type we know how to send (RFC 6750).
      RFC 6749 §7.1: a client must not use a token whose type it doesn't
      understand. Compared case-insensitively, as §5.1 requires.
    - expires_in > 0: with 0 or less, the token would be renewed on every
      call, sending one request to Identity per downstream call.

    RFC 6749 makes `expires_in` only RECOMMENDED. We require it: without it we
    could not know when to renew, and Identity always sends it.
    """

    access_token: str = Field(min_length=1)
    token_type: str
    expires_in: PositiveInt

    @field_validator("token_type")
    @classmethod
    def _must_be_bearer(cls, token_type: str) -> str:
        if token_type.lower() != "bearer":
            raise ValueError(f"unsupported token_type {token_type!r}")
        return token_type


class ClientCredentialsTokenProvider:
    """Fetch, cache and renew one service token (one audience + scopes).

    The OAuth 2.0 client side of the client credentials grant (RFC 6749 §4.4):
    the service authenticates to Identity with its own client ID and secret,
    and gets a token for itself, with no user involved.
    """

    # Renew this long before expiry, so a token is never sent just as it
    # expires (the receiving service checks it a moment later).
    RENEW_MARGIN_SECONDS: ClassVar[float] = 30.0
    GRANT_TYPE: ClassVar[str] = "client_credentials"

    def __init__(
        self,
        *,
        issuer_service: str,
        token_endpoint_url: str,
        client_id: str,
        client_secret: SecretStr,
        audience: str,
        scopes: Iterable[str],
        transport: httpx2.BaseTransport | None = None,  # tests pass a MockTransport
        clock: Callable[[], float] = time.monotonic,  # tests pass a fake clock
    ) -> None:
        """Store the client's credentials; no request is made yet.

        Args:
            issuer_service: Name of the service that issues the tokens (e.g.
                "identity"), like DownstreamClient's `service`. Only used in
                logs and in DownstreamError, so the package doesn't hardcode
                which service that is.
            token_endpoint_url: Full URL of the issuer's token endpoint.
            client_id: This service's client ID at the issuer.
            client_secret: Its secret (a Podman secret, never logged).
            audience: The service the tokens are for (their `aud` claim).
            scopes: The scopes to ask for.
        """
        self._issuer_service: str = issuer_service
        self._token_endpoint_url: str = token_endpoint_url
        self._client_id: str = client_id
        self._client_secret: SecretStr = client_secret
        self._audience: str = audience
        # RFC 6749 §3.3: scopes travel as one space-separated string.
        # Sorted, so the same set always gives the same string.
        self._scope: str = " ".join(sorted(scopes))
        self._clock: Callable[[], float] = clock
        self._client: httpx2.Client = httpx2.Client(
            timeout=DEFAULT_TIMEOUT_SECONDS,
            transport=transport,
        )

        self._token: str | None = None
        self._renew_at: float = 0.0
        # FastAPI runs `def` endpoints in a thread pool: without a lock, two
        # requests arriving together with an expired token would both call
        # Identity. With it, the second one waits and reuses the new token.
        self._lock: threading.Lock = threading.Lock()

    def close(self) -> None:
        self._client.close()

    def get_token(self) -> str:
        """Return a valid service token, calling Identity only when needed.

        This is the only method callers use, before each internal call:
            content.put_json(path, token=provider.get_token(), json=...)

        It returns the cached token while it is fresh. It calls _fetch_token()
        (one HTTP request to Identity) only the first time, and again once the
        token is close to expiry (see renew_margin_seconds). With a 5-minute
        token, that is about one request to Identity every 4.5 minutes, however
        many calls the service makes.
        Same role as Authlib's ensure_active_token().

        Thread-safe: if several requests need a new token at the same time,
        only one of them calls Identity, and the others reuse its token.

        Raises:
            InfrastructureError: Identity is unreachable, timed out, answered
                502/503/504, or sent a malformed body (the client sees 503).
            DownstreamError: Identity refused the request, e.g. 401 for a wrong
                client secret or a client not allowed this audience or scope
                (the client sees 502).
        """
        with self._lock:
            if self._needs_new_token():
                self._fetch_token()
            assert self._token is not None
            return self._token

    def _needs_new_token(self) -> bool:
        """True when there is no token yet, or its renewal time has passed."""
        return self._token is None or self._clock() >= self._renew_at

    def _fetch_token(self) -> None:
        """Ask Identity for a new token and store it, with its renewal time.

        Always makes one HTTP request (OAuth 2.0 client credentials grant,
        RFC 6749 §4.4.2):
            POST <token_endpoint_url>
            Authorization: Basic base64(client_id:client_secret)
            grant_type=client_credentials&audience=...&scope=...

        On success, it updates self._token and self._renew_at, and returns
        nothing. Callers read the token through get_token(). Private: only
        get_token() calls it, while holding the lock, so nothing can skip the
        cache. Same role as Authlib's fetch_token(grant_type="client_credentials")
        (see the module docstring).

        Raises:
            InfrastructureError: Identity is unreachable, timed out, answered
                502/503/504, or sent a body that is not a valid token response.
            DownstreamError: Identity answered another error (e.g. 401 for a
                wrong client secret).
        """
        # Measured before the request: the token's lifetime starts at Identity,
        # so counting from here errs on the safe side.
        #
        # A monotonic clock only moves forward, so changing the system time
        # cannot make an expired token look fresh.
        requested_at: float = self._clock()
        response: httpx2.Response = self._request_token()
        body: _TokenResponse = self._parse_token_response(response)
        self._store_token(body, requested_at)

    def _request_token(self) -> httpx2.Response:
        """Send the client credentials request to Identity's token endpoint.

        The client proves who it is with HTTP Basic authentication
        (`client_secret_basic`): `Authorization: Basic base64(client_id:client_secret)`.
        RFC 6749 §2.3.1 requires every authorization server to support it, and
        marks the alternative (id and secret in the form body,
        `client_secret_post`) as NOT RECOMMENDED. Basic itself is RFC 7617.

        Base64 is an encoding, not encryption: anyone who sees the request can
        read the secret. That is acceptable here because the call never leaves
        the backend network (container to container, never through the gateway).

        `audience` is not in RFC 6749. It tells Identity which service the
        token is for (the token's `aud` claim). The standard name for this is
        `resource` (RFC 8707); both sides are ours, so they only need to agree.

        Raises:
            InfrastructureError: Identity is unreachable, timed out, or
                answered 502/503/504 (the client sees 503).
            DownstreamError: Identity answered another error, e.g. 401 for a
                wrong client secret (the client sees 502).
        """
        try:
            response: httpx2.Response = self._client.post(
                self._token_endpoint_url,
                auth=httpx2.BasicAuth(
                    self._client_id,
                    self._client_secret.get_secret_value(),
                ),
                data={
                    "grant_type": self.GRANT_TYPE,
                    "audience": self._audience,
                    "scope": self._scope,
                },
            )
        except httpx2.TransportError as exc:  # includes timeouts
            logger.warning(
                "%s unreachable for a service token: %s", self._issuer_service, exc
            )
            raise InfrastructureError() from exc

        # 401 here means a wrong client secret (a deployment mistake):
        # it surfaces as DownstreamError -> 502, and is logged.
        raise_for_downstream_error(self._issuer_service, response)
        return response

    def _parse_token_response(self, response: httpx2.Response) -> _TokenResponse:
        """Check that Identity answered a well-formed token response (RFC 6749 §5.1).

        Raises:
            InfrastructureError: The body is not JSON, or a field is missing
                or has the wrong type (the client sees 503).
        """
        try:
            return _TokenResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            # Logged with the issuer's name; the client only gets the generic
            # 503 message, like for any other unavailable dependency.
            logger.warning("Invalid token response from %s", self._issuer_service)
            raise InfrastructureError() from exc

    # Based on https://github.com/googleapis/google-cloud-python/blob/main/packages/google-auth/google/auth/_helpers.py#L42
    def _store_token(self, body: _TokenResponse, requested_at: float) -> None:
        """Cache the token and decide when to renew it.

        Renewing a margin before expiry is common practice: google-auth's
        REFRESH_THRESHOLD, Authlib's `leeway`, Spring's `clockSkew` (see the
        module docstring). Capping the margin at half the lifetime is our own
        addition.
        """
        # The margin is at most half the lifetime, so a token is always used
        # for at least half its life. Without the cap, a token shorter than
        # the margin (e.g. 20 s) would be refetched on every single call.
        margin: float = min(self.RENEW_MARGIN_SECONDS, body.expires_in / 2)
        self._token = body.access_token
        self._renew_at = requested_at + body.expires_in - margin
