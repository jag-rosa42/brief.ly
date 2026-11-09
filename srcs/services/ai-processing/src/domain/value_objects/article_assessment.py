from dataclasses import dataclass
from typing import ClassVar

from src.domain.value_objects.summary import Summary


@dataclass(frozen=True)
class ArticleAssessment:
    MAX_QUALITY_COMMENT_LENGTH: ClassVar[int] = 500

    rejected: bool
    quality_comment: str
    summary: str | None
    generation_duration_ms: int

    def __post_init__(self) -> None:
        if self.generation_duration_ms < 0:
            raise ValueError("Generation duration must be nonnegative")
        if not 1 <= len(self.quality_comment.strip()) <= self.MAX_QUALITY_COMMENT_LENGTH:
            raise ValueError(
                f"Quality comment must contain 1 to "
                f"{self.MAX_QUALITY_COMMENT_LENGTH} characters"
            )
        if self.rejected and self.summary is not None:
            raise ValueError("Rejected articles must not have a summary")
        if not self.rejected:
            try:
                summary = Summary.from_text(self.summary)
            except ValueError as exc:
                raise ValueError(
                    f"Accepted articles need a summary of 1 to "
                    f"{Summary.MAX_LENGTH} characters"
                ) from exc
            object.__setattr__(self, "summary", summary.text)
