from dataclasses import replace
from uuid import UUID

import pytest

from src.application.use_cases.articles import UpdateArticleSummary
from src.domain.entities import ArticleSummary, NormalizedArticle
from src.domain.exception import ArticleNotFoundError
from tests.fixtures.unit_of_work import FakeUnitOfWork


class FakeArticleRepository:
    def __init__(self, article: NormalizedArticle | None) -> None:
        self.article = article
        self.update_count = 0

    def get_by_id(self, article_id: UUID) -> NormalizedArticle | None:
        del article_id
        return self.article

    def update_summary(
        self,
        article_id: UUID,
        summary: ArticleSummary,
    ) -> NormalizedArticle | None:
        del article_id
        self.update_count += 1
        if self.article is None:
            return None
        self.article = replace(
            self.article,
            summary=summary,
        )
        return self.article


class FailingArticleRepository(FakeArticleRepository):
    def update_summary(
        self,
        article_id: UUID,
        summary: ArticleSummary,
    ) -> NormalizedArticle | None:
        raise RuntimeError("persistence failed")


def test_updates_summary_in_one_transaction(
    normalized_article: NormalizedArticle,
    uow: FakeUnitOfWork,
) -> None:
    repository = FakeArticleRepository(normalized_article)
    use_case = UpdateArticleSummary(uow, repository)

    article = use_case.execute(
        article_id=normalized_article.id,
        text="Summary",
        llm_model="test-model",
        rejected=False,
        quality_comment="Looks good",
        generation_duration_ms=1200,
    )

    assert article.summary is not None
    assert article.summary.text == "Summary"
    assert article.summary.llm_model == "test-model"
    assert article.summary.rejected is False
    assert article.summary.quality_comment == "Looks good"
    assert article.summary.generation_duration_ms == 1200
    assert article.summary.summarized_at.tzinfo is not None
    assert repository.update_count == 1
    assert uow.flush_count == 1
    assert uow.commit_count == 1


def test_repeating_the_same_update_preserves_timestamp(
    normalized_article: NormalizedArticle,
    article_summary: ArticleSummary,
    uow: FakeUnitOfWork,
) -> None:
    existing = replace(
        normalized_article,
        summary=article_summary,
    )
    repository = FakeArticleRepository(existing)

    article = UpdateArticleSummary(uow, repository).execute(
        existing.id,
        article_summary.text,
        article_summary.llm_model,
        article_summary.rejected,
        article_summary.quality_comment,
        article_summary.generation_duration_ms,
    )

    assert article.summary == article_summary
    assert repository.update_count == 0
    assert uow.flush_count == 0
    assert uow.commit_count == 0


def test_raises_when_article_does_not_exist(uow: FakeUnitOfWork) -> None:
    repository = FakeArticleRepository(None)

    with pytest.raises(ArticleNotFoundError):
        UpdateArticleSummary(uow, repository).execute(
            UUID("00000000-0000-0000-0000-000000000001"),
            "Summary",
            "test-model",
            False,
            "Looks good",
            1200,
        )

    assert uow.commit_count == 0


def test_rolls_back_and_propagates_unexpected_persistence_errors(
    normalized_article: NormalizedArticle,
    uow: FakeUnitOfWork,
) -> None:
    repository = FailingArticleRepository(normalized_article)

    with pytest.raises(RuntimeError, match="persistence failed"):
        UpdateArticleSummary(uow, repository).execute(
            normalized_article.id,
            "Summary",
            "test-model",
            False,
            "Looks good",
            1200,
        )

    assert uow.commit_count == 0
    assert uow.rollback_count == 1
