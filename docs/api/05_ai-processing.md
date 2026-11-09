# AI Processing (internal only)

AI Processing writes the summaries of articles and topics. It is a **worker**: it has no business routes (only `/health`, and `/metrics` later), and nobody calls it. It runs as commands started by hand inside its container, reads articles from Content Management and writes summaries back there. It is only on the `backend` network. Why it works this way: [06_service-to-service.md](06_service-to-service.md#summaries-an-enrichment-pipeline) and ADR-0010.

| Kind | Method | Service path | Auth | Success | Status |
| --- | --- | --- | --- | --- | --- |
| Internal | GET | `/health` | None | 200 | Done |

On `main`, AI Processing only has `/health`. Its API router still uses the old `/api` prefix (`srcs/services/ai-processing/src/api/routers/__init__.py`) and can be emptied, since the service has no business routes.

| Command | What it does | Calls | Status |
| --- | --- | --- | --- |
| `summarize` (e.g. `make summarize`) | Processes article summaries in a bounded loop, then summarizes every topic from its articles | `GET /internal/v1/articles?summary=missing`, `GET /internal/v1/topics`, `GET /internal/v1/articles?topic_id=`, `PUT .../summary` on Content Management, with its service token | To do |
| `embed` (later) | Stores article embeddings in its own pgvector database | `GET /internal/v1/articles...` on Content Management | To do |

The article-summary loop fetches at most 25 articles per response and uses no
cursor. It stops when Content Management returns an empty list or when AI
Processing reaches three consecutive failures to add summaries to Content
Management. A successful summary write resets the global consecutive-failure
counter to zero.
Each article response includes the stored `content` and `language`; AI
Processing uses the language when generating the summary. For a rejected
article, AI Processing sends `text: null` and `rejected: true` to the article
summary PUT endpoint. Content Management returns `summary: null` and
`read_time_minutes: 0`.
An article marked `rejected: true` has a stored summary row, so it is not
returned by `summary=missing` on subsequent runs. It remains stored for
ingestion deduplication. When collecting articles for a topic summary, AI
Processing uses `GET /internal/v1/articles?topic_id=...`; that list excludes
rejected articles while `GET /internal/v1/topics` still returns every topic.

For each topic, AI Processing sends `text`, `llm_model`, and the non-negative
`generation_duration_ms` measured during generation to
`PUT /internal/v1/topics/{topic_id}/summary`. Content Management stores the
latest summary and returns its text and `summarized_at` in the topic object.

For this guard, the current working definition of a failure is an attempt for an
article that ends without its summary being successfully stored in Content
Management. This definition is provisional and may be refined during development.

Its own database (pgvector) holds only its working data: embeddings, for grouping similar articles and for RAG later. It never stores summaries.
