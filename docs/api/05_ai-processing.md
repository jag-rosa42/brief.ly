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

For this guard, the current working definition of a failure is an attempt for an
article that ends without its summary being successfully stored in Content
Management. This definition is provisional and may be refined during development.

Its own database (pgvector) holds only its working data: embeddings, for grouping similar articles and for RAG later. It never stores summaries.
