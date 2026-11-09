import hmac
import logging
from collections.abc import Iterable
from pathlib import Path

logger: logging.Logger = logging.getLogger(__name__)

# Compared when the client is unknown or has no secret file, so every request
# goes through one comparison and takes about the same time.
_DUMMY_SECRET: bytes = b"no-secret-configured-for-this-client"


class SecretFileClientSecretVerifier:
    """Implements the ClientSecretVerifier port with one secret file per client.

    The file is named `<secrets_dir>/<client_id with _>_client_secret` and lived:
    - in a container at /run/secrets,
    - locally at shared/secrets/services.
    It is read on every request: a request for a token happens about once every five
    minutes per client, and a new secret works without a restart.
    """

    def __init__(
        self,
        secrets_dir: Path,
        known_client_ids: Iterable[str],
    ) -> None:
        self._secrets_dir: Path = secrets_dir
        # Only these IDs ever become a file name. The client ID comes from the
        # request, so without this list "../jwt_private_key" would make us read
        # (and compare against) another secret file.
        self._known_client_ids: frozenset[str] = frozenset(known_client_ids)

    def verify(self, client_id: str, client_secret: str) -> bool:
        expected_secret: bytes | None = self._read_secret(client_id)
        # hmac.compare_digest takes the same time whatever the first wrong
        # byte is; `==` stops at the first difference, which leaks how much
        # of the secret was right.
        matches: bool = hmac.compare_digest(
            client_secret.encode(), expected_secret or _DUMMY_SECRET
        )
        return expected_secret is not None and matches

    def _read_secret(self, client_id: str) -> bytes | None:
        if client_id not in self._known_client_ids:
            return None
        secret_filename: str = f"{client_id.replace('-', '_')}_client_secret"
        path: Path = self._secrets_dir / secret_filename
        try:
            # strip(): pydantic-settings strips secret files too, so a caller
            # reading the same file sends the same value, and a final newline
            # added by an editor doesn't matter.
            secret: str = path.read_text(encoding="utf-8").strip()
        except OSError:
            logger.warning("No secret file for service client %s: %s", client_id, path)
            return None

        if not secret:
            logger.warning("Empty secret file for service client %s: %s", client_id, path)
            return None
        return secret.encode()
