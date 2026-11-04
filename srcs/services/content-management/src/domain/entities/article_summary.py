from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ArticleSummary:
    text: str
    summarized_at: datetime
    llm_model: str
    rejected: bool
    quality_comment: str
    generation_duration_ms: int
