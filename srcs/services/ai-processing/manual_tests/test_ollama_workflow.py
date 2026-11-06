"""Explicit integration test: real host Ollama and fake Content Management."""

from time import perf_counter

from scripts.try_ollama_workflow import (
    ARTICLE_ADDITIONAL_SOURCE_URL,
    ARTICLE_SOURCE_URL,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_URL,
    run_one_article,
)


def test_one_article_with_host_ollama() -> None:
    started = perf_counter()
    fake = run_one_article(DEFAULT_OLLAMA_URL, DEFAULT_MODEL)
    elapsed_seconds = perf_counter() - started

    assert fake.missing_reads == 2
    assert fake.assessment is not None
    assert fake.assessment["rejected"] is False, fake.assessment["quality_comment"]
    assert isinstance(fake.assessment["generation_duration_ms"], int)
    assert fake.assessment["generation_duration_ms"] >= 0
    summary = fake.assessment["text"]
    assert isinstance(summary, str) and summary.strip()
    assert fake.topic_summary is not None
    assert fake.topic_summary["text"] == summary

    print(f"Article source: {ARTICLE_SOURCE_URL}")
    print(f"Additional source: {ARTICLE_ADDITIONAL_SOURCE_URL}")
    print(f"Article summary: {summary}")
    print(f"One-article workflow: {elapsed_seconds:.2f} seconds")
