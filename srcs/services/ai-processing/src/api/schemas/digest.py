"""Request body of the digest route (ADR-0011, docs/api/05_ai-processing.md).

Every field the reader controls is checked here, before anything else runs
(422 VALIDATION_ERROR otherwise). The typing rules are in text_rules.py.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from src.api.schemas.text_rules import TYPED_TEXT_MESSAGE, typed_text
from src.domain.value_objects.digest import FOCUS_MAX_LENGTH, DigestLength


class DigestRequest(BaseModel):
    # extra="forbid": an unknown field is an error, not silently ignored.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    length: DigestLength = DigestLength.SHORT
    # Optional: what matters to the reader today. Empty means no focus.
    focus: Annotated[str, StringConstraints(max_length=FOCUS_MAX_LENGTH)] = ""

    @field_validator("focus")
    @classmethod
    def check_focus(cls, focus: str) -> str:
        if not typed_text.fullmatch(focus):
            raise ValueError(f"The focus {TYPED_TEXT_MESSAGE}")
        return focus
