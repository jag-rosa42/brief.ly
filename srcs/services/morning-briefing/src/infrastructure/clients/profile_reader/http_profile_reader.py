from http import HTTPStatus
from uuid import UUID

from shared_auth import DownstreamClient, DownstreamError

from src.application.exceptions import ProfileReaderUnavailableError
from src.domain.entities.profile import Profile

# Contract: docs/api/02_personalization.md, GET /internal/v1/me/profile.
# DownstreamClient forwards the user's token and translates the errors:
# unreachable or 502/503/504 -> 503, 401 TOKEN_EXPIRED -> 401 TOKEN_EXPIRED,
# any other error -> DownstreamError (502), except the 404 handled below.
# A body that is not the expected JSON -> ProfileReaderUnavailableError (503).
PROFILE_PATH = "/internal/v1/me/profile"
PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"


class HttpProfileReader:
    def __init__(self, client: DownstreamClient) -> None:
        self._client = client

    def get(self, user_token: str) -> Profile | None:
        try:
            data = self._client.get_json(PROFILE_PATH, token=user_token)
        except DownstreamError as error:
            if (
                error.status_code == HTTPStatus.NOT_FOUND
                and error.downstream_code == PROFILE_NOT_FOUND
            ):
                return None
            raise
        except ValueError as error:  # the body is not JSON
            raise ProfileReaderUnavailableError() from error

        try:
            return Profile(
                name=data["name"],
                topic_ids=tuple(data["topic_ids"]),
                saved_article_ids=tuple(UUID(id_) for id_ in data["saved_article_ids"]),
            )
        except (ValueError, KeyError, TypeError) as error:
            raise ProfileReaderUnavailableError() from error
