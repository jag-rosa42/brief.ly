from src.infrastructure.database.repositories import (
    SqlAlchemyNormalizedArticleRepository,
)


def test_exists_returns_true_for_existing_normalized_article(
    db_session,
    source_model,
    normalized_article_model,
):
    db_session.add(source_model)
    db_session.flush()
    db_session.add(normalized_article_model)
    db_session.flush()

    repository = SqlAlchemyNormalizedArticleRepository(db_session)

    assert repository.exists(
        source_id=source_model.id,
        external_id=(normalized_article_model.discovered_article_external_id),
    )
