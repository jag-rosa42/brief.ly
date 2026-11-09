# AI Processing (internal only)

AI Processing assesses and summarizes articles, then summarizes topics. It is a **worker** with no business routes: its HTTP API exposes only `/health`. Run it manually with `make summarize` from the repository root on the host (via SSH to the VM) or `python -m src.worker` inside its container. It reads articles from Content Management and writes results back there. It is only on the `backend` network. See [the service README](../../srcs/services/ai-processing/README.md) for setup.

| Kind | Method | Service path | Auth | Success | Status |
| --- | --- | --- | --- | --- | --- |
| Internal | GET | `/health` | None | 200 | Done |

The health route is registered at the application root, without an `/api` prefix.

| Command | What it does | Calls | Status |
| --- | --- | --- | --- |
| `summarize` (e.g. `make summarize`) | Assesses missing articles, then summarizes each topic from up to 25 returned articles | `GET /internal/v1/articles?summary=missing&limit=25` (default batch size), `GET /internal/v1/topics`, one `GET /internal/v1/articles?topic_id=...&limit=25` per topic, `PUT .../summary` on Content Management | Worker implemented; topic summary PUT pending in Content Management |
| `embed` (later) | Stores article embeddings in its own pgvector database | `GET /internal/v1/articles...` on Content Management | To do |

The article loop uses `ARTICLE_BATCH_SIZE` (default 25) as the request limit and
uses no cursor. It fetches the next batch only after writing an assessment for
every article in the current batch. An empty response ends the article phase;
the first provider, validation, or write failure stops the worker. The topic
phase starts only after the article phase finishes successfully.
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
=======
For each topic, AI Processing reads one list of at most 25 non-rejected articles
from Content Management. Every returned article must have a non-empty stored
summary; otherwise the worker stops without writing that topic. It combines
the summaries in groups of two to four until one remains (a leftover single
summary passes through unchanged) and sends it in the
`text` field of the topic summary PUT. For a topic with no returned articles,
it PUTs `Nothing special happened today, come back later` with
`generation_duration_ms: 0`, without calling the LLM. The selected 25 articles
are determined by Content Management's current query, which has no defined
ordering.

Its pgvector database is provisioned for future working data such as embeddings;
the current worker does not use it or store summaries locally.
