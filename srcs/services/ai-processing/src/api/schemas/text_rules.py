"""What the reader may type in the digest and chat requests (ADR-0011).

There is no SQL to inject: these routes read and write no database. What the
reader types only ever goes into the LLM prompt, so these rules are about
prompt injection (see application/digest_prompt.py). The frontend repeats
them (srcs/frontend/src/features/digest/validation.ts).
"""

import re
from typing import Final

# What the reader types: one line, without "<" or ">" (they could close a
# prompt block early) and without control characters (newlines included).
TYPED_TEXT_PATTERN: Final[str] = r"^[^<>\x00-\x1f\x7f]*$"
TYPED_TEXT_MESSAGE: Final[str] = (
    "must be one line of text without '<', '>' or control characters"
)
# An earlier AI answer: paragraphs (newlines) allowed, other control
# characters not. "<" and ">" are neutralized when the prompt is built.
ANSWER_PATTERN: Final[str] = r"^[^\x00-\x09\x0b-\x1f\x7f]*$"

typed_text: Final[re.Pattern[str]] = re.compile(TYPED_TEXT_PATTERN)
answer_text: Final[re.Pattern[str]] = re.compile(ANSWER_PATTERN)
