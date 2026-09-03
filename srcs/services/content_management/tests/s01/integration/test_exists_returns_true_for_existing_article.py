from src.infrastructure.database.repositories.article_repository import (
        SqlAlchemyArticleRepository,
        )


def test_exists_returns_true_for_existing_article(
    db_session,
    source_model,
    article,
):
    db_session.add(source_model)
    db_session.flush()
    db_session.add(article)
    db_session.flush()

    repository = SqlAlchemyArticleRepository(db_session)

    assert repository.exists(
        source_id=source_model.id,
        external_id=article.external_id,
    )
