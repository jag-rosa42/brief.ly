from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GeneratedApiKey:
    key: str  # the full key, given to the user once and never stored
    prefix: str  # its first characters, stored to recognise it in the list

class ApiKeyGenerator(Protocol):
    """Creates new API keys.

    It doesn't hash them: the use cases do, with the TokenHasher shared with
    refresh tokens, so a key is hashed the same way when it's stored and
    when the gateway asks about it.
    """

    def generate(self) -> GeneratedApiKey: ...
