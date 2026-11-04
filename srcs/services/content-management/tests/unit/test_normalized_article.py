from dataclasses import replace

import pytest

from src.domain.entities import NormalizedArticle


@pytest.mark.parametrize(
    ("word_count", "expected_minutes"),
    [(0, 0), (1, 1), (200, 1), (201, 2), (400, 2)],
)
def test_calculates_read_time_from_article_summary(
    normalized_article: NormalizedArticle,
    word_count: int,
    expected_minutes: int,
) -> None:
    summary = "word " * word_count if word_count else None
    article = replace(normalized_article, summary=summary)

    assert article.read_time_minutes == expected_minutes
