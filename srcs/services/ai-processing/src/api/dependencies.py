from collections.abc import Generator
from functools import lru_cache
from typing import Annotated

import httpx2
from fastapi import Depends
from shared_auth import ClientCredentialsTokenProvider, DownstreamClient
from sqlalchemy.orm import Session

from src.application.ports.digest_writer import DigestWriter
from src.application.ports.profile_reader import ProfileReader
from src.application.ports.topic_catalog import TopicCatalog
from src.application.write_digest import WriteDigest
from src.infrastructure.clients.content_management.http_topic_catalog import (
    HttpTopicCatalog,
)
from src.infrastructure.clients.content_management.service_name import (
    CONTENT_MANAGEMENT_SERVICE,
)
from src.infrastructure.clients.ollama.digest_writer import OllamaDigestWriter
from src.infrastructure.clients.personalization.http_profile_reader import (
    HttpProfileReader,
)
from src.infrastructure.config.digest import DigestSettings
from src.infrastructure.config.service_client import (
    CLIENT_ID,
    CONTENT_MANAGEMENT_AUDIENCE,
    DIGEST_CONTENT_MANAGEMENT_SCOPES,
    TOKEN_PATH,
    ServiceClientSettings,
)
from src.infrastructure.database.config import SessionFactory


def get_db() -> Generator[Session]:
    """
    FastAPI dependency that provides one SQLAlchemy Session per request.

    The Session is automatically closed after the request finishes,
    even if an exception occurs.
    """

    # Create a new Session for this request.
    db = SessionFactory()

    try:
        # Pause here and give the Session to the route handler.
        #
        # FastAPI resumes execution after the endpoint returns,
        # allowing us to perform cleanup.
        yield db
    finally:
        # Return the database connection to SQLAlchemy's connection pool.
        #
        # The Session should not be reused after it is closed.
        db.close()


# Reusable dependency annotation.
#
# Instead of writing:
#
#     db: Session = Depends(get_db)
#
# every time, routes can simply write:
#
#     db: SessionDep
SessionDep = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------------------------
# The digest routes (ADR-0011)
# ---------------------------------------------------------------------------
# Built once, on first use (lru_cache), then every request gets the same
# object: one connection pool per service, one cached service token. The
# worker (src/worker.py) builds its own clients: it runs in another process.


@lru_cache
def get_digest_settings() -> DigestSettings:
    return DigestSettings()


@lru_cache
def get_personalization_client() -> DownstreamClient:
    # The profile belongs to the user: the reader forwards their token.
    return DownstreamClient("personalization", get_digest_settings().PERSONALIZATION_URL)


@lru_cache
def get_content_management_client() -> DownstreamClient:
    return DownstreamClient(
        CONTENT_MANAGEMENT_SERVICE, get_digest_settings().CONTENT_MANAGEMENT_BASE_URL
    )


@lru_cache  # one provider for the whole app, so its cached token is shared
def get_content_management_token_provider() -> ClientCredentialsTokenProvider:
    client_settings = ServiceClientSettings()
    return ClientCredentialsTokenProvider(
        issuer_service="identity",
        token_endpoint_url=f"{client_settings.IDENTITY_URL}{TOKEN_PATH}",
        client_id=CLIENT_ID,
        client_secret=client_settings.AI_PROCESSING_CLIENT_SECRET,
        audience=CONTENT_MANAGEMENT_AUDIENCE,
        scopes=DIGEST_CONTENT_MANAGEMENT_SCOPES,
    )


@lru_cache
def get_ollama_client() -> httpx2.Client:
    return httpx2.Client(base_url=get_digest_settings().OLLAMA_BASE_URL)


@lru_cache
def get_profile_reader() -> ProfileReader:
    return HttpProfileReader(get_personalization_client())


ProfileReaderDep = Annotated[ProfileReader, Depends(get_profile_reader)]


@lru_cache
def get_topic_catalog() -> TopicCatalog:
    return HttpTopicCatalog(
        get_content_management_client(), get_content_management_token_provider()
    )


TopicCatalogDep = Annotated[TopicCatalog, Depends(get_topic_catalog)]


@lru_cache
def get_digest_writer() -> DigestWriter:
    settings = get_digest_settings()
    return OllamaDigestWriter(
        get_ollama_client(), settings.OLLAMA_MODEL, settings.OLLAMA_TIMEOUT_SECONDS
    )


DigestWriterDep = Annotated[DigestWriter, Depends(get_digest_writer)]


def get_write_digest(
    profile_reader: ProfileReaderDep,
    topic_catalog: TopicCatalogDep,
    writer: DigestWriterDep,
) -> WriteDigest:
    return WriteDigest(profile_reader, topic_catalog, writer)


WriteDigestDep = Annotated[WriteDigest, Depends(get_write_digest)]


def close_clients() -> None:
    """Close the HTTP clients and the token provider, when the app stops.

    Only the ones that were created: calling a getter here would build one
    (and, for the token provider, read the client secret) just to close it.
    """
    for getter in (
        get_personalization_client,
        get_content_management_client,
        get_content_management_token_provider,
        get_ollama_client,
    ):
        if getter.cache_info().currsize:
            getter().close()
