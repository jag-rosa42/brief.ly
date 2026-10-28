"""HTTP client for service-to-service calls (ADR-0008).

Calls go directly to the other container by name (http://personalization:8000),
never through the gateway, to /internal/v1/... routes. The receiving service
verifies the token again.

Error mapping, so the frontend always gets a meaningful answer:

    downstream result                    raised here               client sees
    -----------------------------------  ------------------------  -----------------
    connection refused, DNS, timeout     InfrastructureError       503
    502 / 503 / 504                      InfrastructureError       503
    401 with code TOKEN_EXPIRED          TokenExpiredError         401 TOKEN_EXPIRED
    any other 4xx / 5xx                  DownstreamError           502 (or caught)

Standards:
    - RFC 6750 §2.1, sending the token in `Authorization: Bearer <token>`
      https://datatracker.ietf.org/doc/html/rfc6750#section-2.1
    - RFC 9110 §15.6, the 5xx status codes: 502 Bad Gateway, 503 Service
      Unavailable, 504 Gateway Timeout
      https://datatracker.ietf.org/doc/html/rfc9110#section-15.6

Project references:
    - docs/api/00_conventions.md: the error body, the status codes, and why
      TOKEN_EXPIRED must reach the frontend unchanged
    - docs/api/06_service-to-service.md: who calls whom, with which token

Library documentation:
    - httpx clients and connection pooling (same API as httpx2)
      https://www.python-httpx.org/advanced/clients/
    - httpx timeouts
      https://www.python-httpx.org/advanced/timeouts/
    - httpx mock transports, used by the tests
      https://www.python-httpx.org/advanced/transports/#mock-transports
"""

import logging
from http import HTTPStatus
from typing import Any

import httpx2
from shared_errors.exceptions import InfrastructureError

from shared_auth.domain.exceptions import ErrorCode, TokenExpiredError
from shared_auth.infrastructure.clients.exceptions import DownstreamError

logger: logging.Logger = logging.getLogger(__name__)

# httpx applies one number to each step separately (connect, write, read,
# wait for a free connection), not to the whole request. It must stay shorter
# than the frontend's own timeout, so the browser gets our 503 instead of
# giving up first.
DEFAULT_TIMEOUT_SECONDS: float = 5.0

# The answers that mean "the service behind is down or overloaded", not "your
# request is wrong" (RFC 9110 §15.6.3 to §15.6.5).
# http.HTTPStatus (standard library) rather than fastapi.status: only the API
# layer imports FastAPI.
UNAVAILABLE_STATUSES: frozenset[int] = frozenset(
    {
        HTTPStatus.BAD_GATEWAY,
        HTTPStatus.SERVICE_UNAVAILABLE,
        HTTPStatus.GATEWAY_TIMEOUT,
    }
)


def _error_code(response: httpx2.Response) -> str | None:
    """Read `error.code` from a shared-format error body, if there is one."""
    try:
        return response.json()["error"]["code"]
    except ValueError, KeyError, TypeError:
        return None


def raise_for_downstream_error(service: str, response: httpx2.Response) -> None:
    """Translate a downstream error response into our own errors.

    Does nothing on a 2xx answer. Also used by ClientCredentialsTokenProvider
    for Identity's token endpoint.

    Raises:
        InfrastructureError: The service answered 502, 503 or 504 (503).
        TokenExpiredError: The service answered 401 TOKEN_EXPIRED, so the
            token we forwarded expired on the way (401 TOKEN_EXPIRED; the
            frontend refreshes and retries).
        DownstreamError: Any other error answer (502, unless an adapter
            catches it).
    """
    if response.is_success:
        return

    if response.status_code in UNAVAILABLE_STATUSES:
        logger.warning("%s unavailable: HTTP %s", service, response.status_code)
        raise InfrastructureError()

    code: str | None = _error_code(response)

    # The user's token expired somewhere down the chain: tell the frontend
    # exactly that, so it refreshes and retries instead of showing an error.
    if (
        response.status_code == HTTPStatus.UNAUTHORIZED
        and code == ErrorCode.TOKEN_EXPIRED
    ):
        raise TokenExpiredError()

    raise DownstreamError(service, response.status_code, code)


class DownstreamClient:
    """One client per downstream service, created once and reused.

    "Downstream" is the service we call; "upstream" is the one calling us.
    When Morning Briefing calls Personalization, Personalization is downstream
    of Morning Briefing.

    Reusing one httpx2.Client keeps connections open between requests
    (connection pooling). The token is given per call, because it belongs to
    the request being served, not to the client:

        personalization = DownstreamClient("personalization", "http://personalization:8000")
        profile = personalization.get_json("/internal/v1/me/profile", token=user.token)

    The token is either:
        - the user's token,
        - a forwarded unchanged token,
        - or a service token from ClientCredentialsTokenProvider.get_token() (ADR-0008).
    """

    def __init__(
        self,
        service: str,
        base_url: str,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx2.BaseTransport | None = None,  # tests pass a MockTransport
    ) -> None:
        self._service: str = service
        self._client: httpx2.Client = httpx2.Client(
            base_url=base_url,
            timeout=timeout,
            transport=transport,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> httpx2.Response:
        """Call a downstream route with the token; errors become our own errors.

        Returns the response only when it is a 2xx. See the module docstring
        for the full error mapping.

        Raises:
            InfrastructureError: The service is unreachable, timed out, or
                answered 502/503/504 (503).
            TokenExpiredError: The forwarded token expired (401 TOKEN_EXPIRED).
            DownstreamError: Any other error answer (502, unless caught).
        """
        response: httpx2.Response = self._send(
            method,
            path,
            token=token,
            params=params,
            json=json,
        )
        raise_for_downstream_error(self._service, response)
        return response

    def _send(
        self,
        method: str,
        path: str,
        *,
        token: str,
        params: dict[str, Any] | None,
        json: Any,
    ) -> httpx2.Response:
        """Send the request with the Bearer token (RFC 6750 §2.1).

        Network failures become InfrastructureError (503). Error answers
        (4xx, 5xx) are returned as is: request() translates them.
        """
        try:
            return self._client.request(
                method,
                path,
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {token}"},
            )
        except httpx2.TimeoutException as exc:
            logger.warning("%s timed out: %s %s", self._service, method, path)
            raise InfrastructureError() from exc
        except httpx2.TransportError as exc:
            # Connection refused, unknown host (container stopped), reset...
            logger.warning("%s unreachable: %s", self._service, exc)
            raise InfrastructureError() from exc

    def get_json(
        self, path: str, *, token: str, params: dict[str, Any] | None = None
    ) -> Any:
        """GET a route and return its decoded JSON body. Errors: see request()."""
        return self.request("GET", path, token=token, params=params).json()

    def post_json(self, path: str, *, token: str, json: Any = None) -> Any:
        """POST a JSON body and return the decoded JSON answer. Errors: see request()."""
        return self.request("POST", path, token=token, json=json).json()

    def put_json(self, path: str, *, token: str, json: Any = None) -> Any:
        """PUT a JSON body and return the decoded JSON answer. Errors: see request().

        E.g. AI Processing storing a summary in Content Management (ADR-0010).
        """
        return self.request("PUT", path, token=token, json=json).json()

    def close(self) -> None:
        self._client.close()
