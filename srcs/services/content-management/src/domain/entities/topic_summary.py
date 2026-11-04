from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TopicSummary:
    text: str
    summarized_at: datetime
    llm_model: str
