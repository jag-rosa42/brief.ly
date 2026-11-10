import secrets
from typing import ClassVar

from src.application.port.api_key.generator import GeneratedApiKey


class SecretsApiKeyGenerator:
    """API keys made with Python's `secrets` module (ADR-0009).

    A key looks like `tr_` followed by 43 URL-safe characters:

        tr_8f3kQ1x...

    - `tr_` makes our keys recognisable, by people and by secret scanners
      (e.g. a key pasted in a public repository).
    - The random part is 32 bytes (256 bits) from the operating system's
      secure random source, so it can't be guessed.
    """

    KEY_PREFIX: ClassVar[str] = "tr_"
    RANDOM_BYTES: ClassVar[int] = 32
    # Random characters kept in the stored prefix ("tr_8f3k"): enough for the
    # user to tell keys apart, far too few to help guess the key.
    VISIBLE_RANDOM_CHARS: ClassVar[int] = 4

    def generate(self) -> GeneratedApiKey:
        key: str = f"{self.KEY_PREFIX}{secrets.token_urlsafe(self.RANDOM_BYTES)}"
        return GeneratedApiKey(
            key=key,
            prefix=key[: len(self.KEY_PREFIX) + self.VISIBLE_RANDOM_CHARS],
        )
