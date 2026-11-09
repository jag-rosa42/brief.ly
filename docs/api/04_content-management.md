# Content Management (internal only)

Content Management collects articles from external providers, normalizes them, and owns the topics. It is also where **summaries are stored**: AI Processing writes them, everyone else reads them here (see [06_service-to-service.md](06_service-to-service.md#summaries-an-enrichment-pipeline)). It is only on the `backend` network, so it only exposes Internal routes, and it doesn't call any other service. Its data belongs to no user, so callers use a service token. Conventions, tokens and errors are in [00_conventions.md](00_conventions.md).

A topic is never hard-deleted, so a profile can never point at a missing topic. Topic IDs are NewsAPI categories (`"business"`, `"technology"`...), seeded by the migration `srcs/services/content-management/migrations/versions/df8dd7662ec0_add_topics_table.py`.

| Kind | Method | Service path | Auth | Success | Status |
| --- | --- | --- | --- | --- | --- |
| Internal | POST | `/internal/v1/ingestion-runs` | Service (`ingestion:run`) | 201 | Partial (token check missing) |
| Internal | GET | `/internal/v1/topics` | Service (`topics:read`) | 200 | Partial (token check missing) |
| Internal | GET | `/internal/v1/articles?topic_id={topic_id}` | Service (`articles:read`) | 200 | Partial (token check missing) |
| Internal | GET | `/internal/v1/articles?summary=missing` | Service (`articles:read`) | 200 | Partial (token check missing) |
| Internal | GET | `/internal/v1/articles/{article_id}` | Service (`articles:read`) | 200 | Partial (token check missing) |
| Internal | PUT | `/internal/v1/articles/{article_id}/summary` | Service (`summaries:write`) | 200 | Partial (token check missing) |
| Internal | PUT | `/internal/v1/topics/{topic_id}/summary` | Service (`summaries:write`) | 200 | Partial (token check missing) |
| Internal | GET | `/health` | None | 200 | Done |

**The topic GET and summary PUT routes are Partial.** The GET returns `id`,
`summary`, and `summarized_at`; the PUT creates or replaces the latest summary.
Neither route checks a service token yet (the known gap below).

**`POST /internal/v1/ingestion-runs` is Partial.** It triggers a synchronous ingestion and reports whether it succeeded fully or partially, but does not check a service token yet.

- Only AI Processing's client may get the `summaries:write` scope (Identity's client registry, ADR-0008).
- Known gap: until service tokens exist (ADR-0008), these routes are unauthenticated and protected only by not being routed and by the `backend` network. Service tokens are built before the Public API.
- The article GET routes and article summary PUT route exist. The article GET routes apply the rejection rules below.

The article object, used by every article endpoint:

Content Management owns `read_time_minutes` as a derived, non-persisted field.
It calculates the estimated reading time from the stored `summary`, rounded up
at 200 words per minute. The value is `0` when `summary` is `null`,
including after rejection; AI Processing does not calculate or send it.

```text
{
  "article_id": UUID,
  "title": str,
  "publisher_name": str,
  "url": str,
  "topic_id": str,
  "language": str,                stored article language
  "content": str,                  stored article text used by AI Processing
  "read_time_minutes": int,
  "summary": str | null,             null before summarization or after rejection
  "summarized_at": datetime | null,
  "rejected": bool | null,
  "quality_comment": str | null,
  "generation_duration_ms": int | null
}
```

Article summaries are persisted in the dedicated `article_summaries` table,
with `article_id` as both primary key and foreign key. Therefore an article has
at most one current summary, and the absence of a row represents a missing
summary. `generation_duration_ms` is a non-negative duration measured by AI
Processing; the explicit millisecond suffix is part of the contract.
`rejected` is `null` before an article summary exists, then `true` or `false`
as decided by AI Processing. A rejected article stays in Content Management
for ingestion deduplication, but read endpoints do not expose it to consumers.
A rejected article keeps its summary row, with `text` set to SQL `NULL`; it
is not selected again by `summary=missing`. The summary write response is the
exception to the read restriction: it returns the updated article with
`rejected: true`, `summary: null`, and `read_time_minutes: 0`.

The topic object:

```text
{
  "id": str,                         e.g. "business"
  "summary": str | null,             latest topic summary, null until the first summary run
  "summarized_at": datetime | null
}
```

Topic summaries use a dedicated `topic_summaries` table, with `topic_id` as
both primary key and foreign key. As with article summaries, the absence of a
row means no summary has been generated. Topic summaries share the common
`text`, `summarized_at`, `llm_model`, and `generation_duration_ms` fields;
article quality metadata is specific to article summaries. The duration is
measured by AI Processing in non-negative milliseconds. It is required on new
summary writes but nullable in storage so summaries created before the duration
was added remain available.

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
The catalog always includes every configured topic, even when all its articles
have been rejected. Topics have no `rejected` status of their own. A topic
summary must be generated only from articles returned by the topic article
query, which excludes rejected articles.

### GET /internal/v1/articles

Two filters, exactly one of them required:

| Query | Used by | Returns |
| --- | --- | --- |
| `topic_id={topic_id}` | Morning Briefing and AI Processing | The topic's articles except those with `rejected: true`, with their summaries |
| `summary=missing` | AI Processing | Articles with no row in `article_summaries` yet |

`limit` (optional, 1-25, default 25) caps the number of items. A response never
contains more than 25 articles. The endpoint does not accept or return a cursor.

Articles are not sorted chronologically, and consumers do not distinguish recent
articles from older ones. Articles have no expiration or automatic deletion: once
stored, they remain in the database. This does not affect `summarized_at`, which is
metadata about summary generation rather than article age.
The topic filter includes articles without a summary (`rejected: null`) and
articles with `rejected: false`; it excludes articles with `rejected: true`
before applying `limit`. This also ensures topic summaries are based only on
eligible articles. For `summary=missing`, a rejected summary still counts as
an existing summary and is not retried automatically. The limit applies after
the filter, so rejected articles cannot fill response slots.
AI Processing reads `content` from these article responses to generate summaries.

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

Used by Personalization when an article is saved: the response already contains the summary, which goes into the saved-article snapshot. An article with `rejected: true` is treated as unavailable to readers, even though its row remains stored for deduplication.

```text
Header: Authorization: Bearer <service token>

200 OK                <article>
401 Unauthorized
403 Forbidden         INSUFFICIENT_SCOPE
404 Not Found         ARTICLE_NOT_FOUND (unknown or rejected article)
```

### PUT /internal/v1/articles/{article_id}/summary

Called by AI Processing's summary command. Creates or replaces the article's summary (idempotent: sending the same summary twice changes nothing).

```text
Header: Authorization: Bearer <service token with summaries:write>
Body:
{
  "text": str | null,          1-2000 chars in the article's language if accepted;
                                 null if rejected (never an empty string)
  "llm_model": str,            stored for traceability, not returned
  "rejected": bool,
  "quality_comment": str,      0-2000 chars
  "generation_duration_ms": int  non-negative duration measured by AI Processing
}

200 OK                <article>, with quality metadata set; if rejected,
                      summary is null and read_time_minutes is 0
401 Unauthorized
403 Forbidden         INSUFFICIENT_SCOPE
404 Not Found         ARTICLE_NOT_FOUND
422 Unprocessable     VALIDATION_ERROR
```

### PUT /internal/v1/topics/{topic_id}/summary

Called by AI Processing's summary command. Replaces the topic's latest summary; older ones are not kept.
Each successful PUT updates `summarized_at`, even if the text is unchanged.

```text
Header: Authorization: Bearer <service token with summaries:write>
Body:
{
  "text": str,                 1-2000 chars
  "llm_model": str,            stored for traceability, not returned
  "generation_duration_ms": int  non-negative duration measured by AI Processing
}

200 OK                <topic>, with summary and summarized_at set
401 Unauthorized
403 Forbidden         INSUFFICIENT_SCOPE
404 Not Found         TOPIC_NOT_FOUND
422 Unprocessable     VALIDATION_ERROR
```
