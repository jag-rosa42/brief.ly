from collections.abc import Iterator
from typing import Protocol

from src.application.digest_prompt import Prompt


class DigestWriter(Protocol):
    def write(self, prompt: Prompt) -> Iterator[str]:
        """Send the prompt to the LLM and yield its answer, piece by piece.

        Lazy: nothing is sent before the first piece is asked for, so the
        caller can return its response headers first and stream the answer.

        Raises (while iterating):
            InfrastructureError: if the LLM can't be reached or fails mid-answer.
        """
        ...
