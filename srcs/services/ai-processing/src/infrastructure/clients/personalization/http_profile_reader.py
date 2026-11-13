from http import HTTPStatus

from shared_auth import DownstreamClient, DownstreamError

from src.application.exceptions import ProfileReaderUnavailableError

# Contract: docs/api/02_personalization.md, GET /internal/v1/me/profile.
# Same reader as Morning Briefing's (its http_profile_reader.py), keeping only
# the topics. DownstreamClient forwards the user's token and translates the
# errors: unreachable or 502/503/504 -> 503, 401 TOKEN_EXPIRED -> 401
# TOKEN_EXPIRED (the frontend refreshes and retries), any other error ->
# DownstreamError (502), except the 404 handled below. A body that is not the
# expected JSON -> ProfileReaderUnavailableError (503).
PROFILE_PATH = "/internal/v1/me/profile"
PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"


class HttpProfileReader:
    def __init__(self, client: DownstreamClient) -> None:
        self._client = client

    def get_topic_ids(self, user_token: str) -> tuple[str, ...]:
        try:
            data = self._client.get_json(PROFILE_PATH, token=user_token)
        except DownstreamError as error:
            if (
                error.status_code == HTTPStatus.NOT_FOUND
                and error.downstream_code == PROFILE_NOT_FOUND
            ):
                return ()  # no profile yet: no topics
            raise
        except ValueError as error:  # the body is not JSON
            raise ProfileReaderUnavailableError() from error

        try:
            topic_ids = data["topic_ids"]
            if not isinstance(topic_ids, list) or not all(
                isinstance(topic_id, str) for topic_id in topic_ids
            ):
                raise TypeError("topic_ids must be a list of strings")
            return tuple(topic_ids)
        except (KeyError, TypeError) as error:
            raise ProfileReaderUnavailableError() from error
