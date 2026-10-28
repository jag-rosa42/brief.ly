from src.infrastructure.database.repositories import (
    SqlAlchemyNormalizedArticleRepository,
)


def test_returns_existing_external_ids_for_source(
    db_session,
    source_model,
    normalized_article_model,
):
    db_session.add(source_model)
    db_session.flush()
    db_session.add(normalized_article_model)
    db_session.flush()

    repository = SqlAlchemyNormalizedArticleRepository(db_session)

    existing_external_ids = repository.find_existing_external_ids(
        source_id=source_model.id,
        external_ids=[
            normalized_article_model.discovered_article_external_id,
            "missing-article",
        ],
    )

    assert existing_external_ids == {
        normalized_article_model.discovered_article_external_id
    }
