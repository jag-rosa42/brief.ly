from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Topic:
    id: str
    summary: str | None = None
    summarized_at: datetime | None = None
    summary_llm_model: str | None = None
