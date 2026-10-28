"""
DownstreamClient: token forwarding, and the error mapping of the module
docstring. The downstream service is an httpx2.MockTransport handler.
"""

from collections.abc import Callable

import httpx2
import pytest
from shared_errors import InfrastructureError

from shared_auth.domain.exceptions import TokenExpiredError
from shared_auth.infrastructure.clients.downstream_client import DownstreamClient
from shared_auth.infrastructure.clients.exceptions import DownstreamError
from tests.fixtures.clients import DOWNSTREAM_BASE_URL, DOWNSTREAM_SERVICE, Handler
from tests.fixtures.factory import build_error_response
from tests.fixtures.http import Routes

MakeClient = Callable[[Handler], DownstreamClient]


class TestForwarding:
    def test_get_json_forwards_the_token_unchanged(
        self, make_downstream_client: MakeClient
    ) -> None:
        seen: list[httpx2.Request] = []

        def handler(request: httpx2.Request) -> httpx2.Response:
            seen.append(request)
            return httpx2.Response(200, json=[{"id": 1}, {"id": 2}])

        resources = make_downstream_client(handler).get_json(
            Routes.DOWNSTREAM_RESOURCE, token="user-token", params={"limit": 5}
        )

        assert resources == [{"id": 1}, {"id": 2}]
        assert seen[0].method == "GET"
        assert seen[0].headers["Authorization"] == "Bearer user-token"
        assert (
            str(seen[0].url)
            == f"{DOWNSTREAM_BASE_URL}{Routes.DOWNSTREAM_RESOURCE}?limit=5"
        )

    def test_post_json(self, make_downstream_client: MakeClient) -> None:
        seen: list[httpx2.Request] = []

        def handler(request: httpx2.Request) -> httpx2.Response:
            seen.append(request)
            return httpx2.Response(201, json={"id": 1})

        body = make_downstream_client(handler).post_json(
            Routes.DOWNSTREAM_RESOURCE, token="t", json={"a": 1}
        )

        assert body == {"id": 1}
        assert seen[0].method == "POST"
        assert seen[0].content == b'{"a":1}'

    def test_put_json(self, make_downstream_client: MakeClient) -> None:
        seen: list[httpx2.Request] = []

        def handler(request: httpx2.Request) -> httpx2.Response:
            seen.append(request)
            return httpx2.Response(200, json={"name": "updated"})

        body = make_downstream_client(handler).put_json(
            f"{Routes.DOWNSTREAM_RESOURCE}/1", token="t", json={"name": "updated"}
        )

        assert body == {"name": "updated"}
        assert seen[0].method == "PUT"
        assert seen[0].headers["Authorization"] == "Bearer t"

    def test_request_returns_the_response(
        self, make_downstream_client: MakeClient
    ) -> None:
        # For answers without a JSON body (e.g. 204 No Content).
        response: httpx2.Response = make_downstream_client(
            lambda _request: httpx2.Response(204)
        ).request("DELETE", f"{Routes.DOWNSTREAM_RESOURCE}/1", token="t")

        assert response.status_code == 204


class TestNetworkErrors:
    @pytest.mark.parametrize(
        "error",
        [
            httpx2.ConnectError("connection refused"),  # container stopped
            httpx2.ConnectError("name resolution failed"),  # unknown host
            httpx2.ReadTimeout("too slow"),
            httpx2.ConnectTimeout("too slow"),
        ],
    )
    def test_becomes_infrastructure_error(
        self, make_downstream_client: MakeClient, error: httpx2.TransportError
    ) -> None:
        def handler(_request: httpx2.Request) -> httpx2.Response:
            raise error

        with pytest.raises(InfrastructureError):
            make_downstream_client(handler).get_json("/x", token="t")


class TestErrorAnswers:
    @pytest.mark.parametrize("status_code", [502, 503, 504])
    def test_unavailable_statuses_become_infrastructure_error(
        self, make_downstream_client: MakeClient, status_code: int
    ) -> None:
        client: DownstreamClient = make_downstream_client(
            lambda _request: httpx2.Response(status_code)
        )

        with pytest.raises(InfrastructureError):
            client.get_json("/x", token="t")

    def test_token_expired_is_passed_on(self, make_downstream_client: MakeClient) -> None:
        client: DownstreamClient = make_downstream_client(
            lambda _request: build_error_response(401, "TOKEN_EXPIRED")
        )

        with pytest.raises(TokenExpiredError):
            client.get_json("/x", token="t")

    def test_other_401_becomes_downstream_error(
        self, make_downstream_client: MakeClient
    ) -> None:
        client: DownstreamClient = make_downstream_client(
            lambda _request: build_error_response(401, "INVALID_TOKEN")
        )

        with pytest.raises(DownstreamError) as error:
            client.get_json("/x", token="t")

        assert error.value.service == DOWNSTREAM_SERVICE
        assert error.value.status_code == 401
        assert error.value.downstream_code == "INVALID_TOKEN"

    def test_404_becomes_downstream_error_the_adapter_can_catch(
        self, make_downstream_client: MakeClient
    ) -> None:
        client: DownstreamClient = make_downstream_client(
            lambda _request: build_error_response(404, "NOT_FOUND")
        )

        with pytest.raises(DownstreamError) as error:
            client.get_json("/x", token="t")

        assert error.value.status_code == 404

    @pytest.mark.parametrize(
        "response",
        [
            httpx2.Response(500, text="boom"),  # not JSON
            httpx2.Response(500, json={"detail": "x"}),  # FastAPI's default format
            httpx2.Response(500, json=["unexpected"]),  # JSON, wrong shape
        ],
    )
    def test_error_without_a_shared_format_body(
        self, make_downstream_client: MakeClient, response: httpx2.Response
    ) -> None:
        client: DownstreamClient = make_downstream_client(lambda _request: response)

        with pytest.raises(DownstreamError) as error:
            client.get_json("/x", token="t")

        assert error.value.downstream_code is None


class TestClose:
    def test_close_closes_the_connection_pool(
        self, make_downstream_client: MakeClient
    ) -> None:
        client: DownstreamClient = make_downstream_client(
            lambda _request: httpx2.Response(200, json={})
        )

        client.close()

        with pytest.raises(RuntimeError):
            client.get_json("/x", token="t")
