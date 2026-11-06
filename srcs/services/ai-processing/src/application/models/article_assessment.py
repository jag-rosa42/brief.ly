from dataclasses import dataclass


@dataclass(frozen=True)
class ArticleAssessment:
    rejected: bool
    quality_comment: str
    summary: str | None
    generation_duration_ms: int

    def __post_init__(self) -> None:
        if self.generation_duration_ms < 0:
            raise ValueError("Generation duration must be nonnegative")
        if not 1 <= len(self.quality_comment.strip()) <= 500:
            raise ValueError("Quality comment must contain 1 to 500 characters")
        if self.rejected and self.summary is not None:
            raise ValueError("Rejected articles must not have a summary")
        if not self.rejected and (
            self.summary is None or not 1 <= len(self.summary.strip()) <= 2000
        ):
            raise ValueError("Accepted articles need a summary of 1 to 2000 characters")
