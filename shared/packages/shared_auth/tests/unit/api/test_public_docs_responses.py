"""OpenApiResponse: what the docs show for one status code."""

from shared_errors import ErrorResponse

from shared_auth.api.public_docs import (
    PUBLIC_API_RESPONSES,
    OpenApiHeader,
    OpenApiResponse,
    to_fastapi_responses,
)


class TestOpenApiResponse:
    def test_a_description_alone(self) -> None:
        assert OpenApiResponse(description="Not found").to_fastapi() == {
            "description": "Not found"
        }

    def test_with_a_body_model(self) -> None:
        response = OpenApiResponse(description="Refused", model=ErrorResponse)

        assert response.to_fastapi() == {
            "description": "Refused",
            "model": ErrorResponse,
        }

    def test_with_headers(self) -> None:
        response = OpenApiResponse(
            description="Slow down",
            headers=(OpenApiHeader("Retry-After", "Seconds to wait", "integer"),),
        )

        assert response.to_fastapi()["headers"] == {
            "Retry-After": {
                "description": "Seconds to wait",
                "schema": {"type": "integer"},
            }
        }

    def test_several_in_fastapi_shape(self) -> None:
        responses = to_fastapi_responses(
            {
                401: OpenApiResponse(description="Who are you?"),
                403: OpenApiResponse(description="Not allowed"),
            }
        )

        assert responses == {
            401: {"description": "Who are you?"},
            403: {"description": "Not allowed"},
        }


class TestPublicApiResponses:
    def test_documents_the_three_gateway_errors(self) -> None:
        assert set(PUBLIC_API_RESPONSES) == {401, 403, 429}

    def test_the_errors_from_our_services_use_the_shared_format(self) -> None:
        assert PUBLIC_API_RESPONSES[401]["model"] is ErrorResponse
        assert PUBLIC_API_RESPONSES[403]["model"] is ErrorResponse

    def test_the_429_is_traefik_plain_text_with_retry_after(self) -> None:
        too_many = PUBLIC_API_RESPONSES[429]

        assert "model" not in too_many
        assert "Retry-After" in too_many["headers"]
