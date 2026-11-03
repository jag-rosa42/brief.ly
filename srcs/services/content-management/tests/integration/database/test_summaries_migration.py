import pytest
from sqlalchemy import DateTime, String, inspect
from sqlalchemy.orm import Session

SUMMARY_TABLES = ("normalized_articles", "topics")


@pytest.mark.integration
@pytest.mark.parametrize("table_name", SUMMARY_TABLES)
def test_migration_adds_nullable_summary_columns(
    db_session: Session,
    table_name: str,
):
    columns = {
        column["name"]: column
        for column in inspect(db_session.connection()).get_columns(table_name)
    }

    summary = columns["summary"]
    assert isinstance(summary["type"], String)
    assert summary["type"].length == 2000
    assert summary["nullable"]

    summarized_at = columns["summarized_at"]
    assert isinstance(summarized_at["type"], DateTime)
    assert summarized_at["type"].timezone
    assert summarized_at["nullable"]

    summary_llm_model = columns["summary_llm_model"]
    assert isinstance(summary_llm_model["type"], String)
    assert summary_llm_model["nullable"]
