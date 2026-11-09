import pytest

from src.domain.value_objects.article_assessment import ArticleAssessment
from src.domain.value_objects.summary import Summary


def test_from_text_strips_and_preserves_summary_value() -> None:
    assert Summary.from_text("  A short summary. \n") == Summary("A short summary.")


@pytest.mark.parametrize("raw", [None, "", "   ", "x" * 2001])
def test_from_text_rejects_missing_or_oversized_summary(raw: str | None) -> None:
    with pytest.raises(ValueError, match="Summary must contain"):
        Summary.from_text(raw)


def test_direct_constructor_rejects_untrimmed_text() -> None:
    with pytest.raises(ValueError, match="stripped characters"):
        Summary(" A short summary. ")


def test_article_assessment_normalizes_accepted_summary() -> None:
    assessment = ArticleAssessment(False, "Complete article", "  A short summary.  ", 12)

    assert assessment.summary == "A short summary."
