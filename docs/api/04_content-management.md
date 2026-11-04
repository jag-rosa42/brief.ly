# Content Management (internal only)

Content Management collects articles from external providers, normalizes them, and owns the topics. It is also where **summaries are stored**: AI Processing writes them, everyone else reads them here (see [06_service-to-service.md](06_service-to-service.md#summaries-an-enrichment-pipeline)). It is only on the `backend` network, so it only exposes Internal routes, and it doesn't call any other service. Its data belongs to no user, so callers use a service token. Conventions, tokens and errors are in [00_conventions.md](00_conventions.md).

A topic is never hard-deleted, so a profile can never point at a missing topic. Topic IDs are NewsAPI categories (`"business"`, `"technology"`...), seeded by the migration `srcs/services/content-management/migrations/versions/df8dd7662ec0_add_topics_table.py`.

| Kind | Method | Service path | Auth | Success | Status |
| --- | --- | --- | --- | --- | --- |
| Internal | POST | `/internal/v1/ingestion-runs` | Service (`ingestion:run`) | 201 | Partial (see below) |
| Internal | GET | `/internal/v1/topics` | Service (`topics:read`) | 200 | Partial (see below) |
| Internal | GET | `/internal/v1/articles?topic_id={topic_id}` | Service (`articles:read`) | 200 | To do |
| Internal | GET | `/internal/v1/articles?summary=missing` | Service (`articles:read`) | 200 | To do |
| Internal | GET | `/internal/v1/articles/{article_id}` | Service (`articles:read`) | 200 | To do |
| Internal | PUT | `/internal/v1/articles/{article_id}/summary` | Service (`summaries:write`) | 200 | To do |
| Internal | PUT | `/internal/v1/topics/{topic_id}/summary` | Service (`summaries:write`) | 200 | To do |
| Internal | GET | `/health` | None | 200 | Done |

**`GET /internal/v1/topics` is Partial.** It exists on `main` (`srcs/services/content-management/src/api/routers/topics/router.py`, schema `srcs/services/content-management/src/api/schemas/topic.py`), with two things missing:
1. Topics have no `summary` / `summarized_at` yet (ADR-0010).
2. No token is checked yet (the known gap below; service tokens are not built yet).

**`POST /internal/v1/ingestion-runs` is Partial.** It triggers a synchronous ingestion and reports whether it succeeded fully or partially, but does not check a service token yet.

- Only AI Processing's client may get the `summaries:write` scope (Identity's client registry, ADR-0008).
- Known gap: until service tokens exist (ADR-0008), these routes are unauthenticated and protected only by not being routed and by the `backend` network. Service tokens are built before the Public API.

The article object, used by every article endpoint:

Content Management owns `read_time_minutes` as a derived, non-persisted field.
It calculates the estimated reading time from the stored `summary`, rounded up
at 200 words per minute. The value is `0` while `summary` is `null`; AI
Processing does not calculate or send it.

```text
{
  "article_id": UUID,
  "title": str,
  "source": str,
  "url": str,
  "topic_id": str,
  "read_time_minutes": int,
  "summary": str | null,             null until AI Processing has summarized it
  "summarized_at": datetime | null
}
```

The topic object:

```text
{
  "id": str,                         e.g. "business"
  "summary": str | null,             latest topic summary, null until the first summary run
  "summarized_at": datetime | null
}
```

## Endpoint details

Each endpoint below shows the request and every possible response.

### POST /internal/v1/ingestion-runs

Fetches new articles (with newspaper3k) and stores them, with `summary: null`. It is started manually with `make ingest`; a source becomes eligible again after 30 minutes.

An ingestion is partially successful when at least one article was stored despite other article or source failures. It fails only when errors occurred and no article was stored. A run without errors remains successful when there was no new article to store. Only one ingestion may run at a time; a concurrent request is rejected without waiting.

```text
Header: Authorization: Bearer <service token>
Body: none

201 Created           {"status": "succeeded" | "partial"}
502 Bad Gateway
{
  "error": {
    "code": "INGESTION_FAILED",
    "message": "Article ingestion completed with errors."
  }
}
409 Conflict             INGESTION_ALREADY_RUNNING
500 Internal Server Error INTERNAL_SERVER_ERROR
401 Unauthorized
403 Forbidden         INSUFFICIENT_SCOPE
```

### GET /internal/v1/topics

```text
Header: Authorization: Bearer <service token>

200 OK
[<topic>]                             currently 7 topics
401 Unauthorized
403 Forbidden         INSUFFICIENT_SCOPE
```

Exception to the `{"items": [...]}` convention: this route returns a bare array, as implemented on `main`. Accepted for now (decided 2026-10-20) to save time; to align with the other lists later.

### GET /internal/v1/articles

Two filters, exactly one of them required:

| Query | Used by | Returns |
| --- | --- | --- |
| `topic_id={topic_id}` | Morning Briefing | The topic's articles, with their summaries |
| `summary=missing` | AI Processing | Articles that have no summary yet. ~~Oldest first.~~ |

`limit` (optional, 1-25, default 25) caps the number of items. A response never
contains more than 25 articles. The endpoint does not accept or return a cursor.

Articles are not sorted chronologically, and consumers do not distinguish recent
articles from older ones. Articles have no expiration or automatic deletion: once
stored, they remain in the database. This does not affect `summarized_at`, which is
metadata about summary generation rather than article age.

```text
Header: Authorization: Bearer <service token>

200 OK
{
  "items": [<article>]          [] when nothing matches
}
401 Unauthorized
403 Forbidden         INSUFFICIENT_SCOPE
404 Not Found         TOPIC_NOT_FOUND
422 Unprocessable     VALIDATION_ERROR (no filter or both filters,
                      summary not "missing", limit out of range)
```

### GET /internal/v1/articles/{article_id}

Used by Personalization when an article is saved: the response already contains the summary, which goes into the saved-article snapshot.

```text
Header: Authorization: Bearer <service token>

200 OK                <article>
401 Unauthorized
403 Forbidden         INSUFFICIENT_SCOPE
404 Not Found         ARTICLE_NOT_FOUND
```

### PUT /internal/v1/articles/{article_id}/summary

Called by AI Processing's summary command. Creates or replaces the article's summary (idempotent: sending the same summary twice changes nothing).

```text
Header: Authorization: Bearer <service token with summaries:write>
Body:
{
  "summary": str,              1-2000 chars, written in the article's language
  "summary_llm_model": str             stored (column summary_llm_model) for traceability, not returned
}

200 OK                <article>, with summary and summarized_at set
401 Unauthorized
403 Forbidden         INSUFFICIENT_SCOPE
404 Not Found         ARTICLE_NOT_FOUND
422 Unprocessable     VALIDATION_ERROR
```

### PUT /internal/v1/topics/{topic_id}/summary

Called by AI Processing's summary command. Replaces the topic's latest summary; older ones are not kept.

```text
Header: Authorization: Bearer <service token with summaries:write>
Body:
{
  "summary": str,              1-2000 chars
  "summary_llm_model": str             stored (column summary_llm_model) for traceability, not returned
}

200 OK                <topic>, with summary and summarized_at set
401 Unauthorized
403 Forbidden         INSUFFICIENT_SCOPE
404 Not Found         TOPIC_NOT_FOUND
422 Unprocessable     VALIDATION_ERROR
```
