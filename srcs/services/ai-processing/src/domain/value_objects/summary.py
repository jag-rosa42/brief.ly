from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Summary:
    MAX_LENGTH: ClassVar[int] = 2000  # Content Management's summary contract.

    text: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.text, str)
            or not 1 <= len(self.text) <= self.MAX_LENGTH
            or self.text != self.text.strip()
        ):
            raise ValueError(
                f"Summary must contain 1 to {self.MAX_LENGTH} stripped characters"
            )

    @classmethod
    def from_text(cls, raw: str | None) -> Summary:
        if not isinstance(raw, str):
            raise ValueError(
                f"Summary must contain 1 to {cls.MAX_LENGTH} stripped characters"
            )
        return cls(raw.strip())
