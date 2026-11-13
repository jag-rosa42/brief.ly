# AI Processing

AI Processing does two things with the LLM:

- **The summary worker** assesses and summarizes articles, then summarizes topics. Run it manually with `make summarize` from the repository root on the host (via SSH to the VM) or `python -m src.worker` inside its container. It reads articles from Content Management and writes results back there (ADR-0010).
- **The digest and its chat** (ADR-0011): two Frontend routes that write, on request, a digest of the user's topics and answer follow-up questions about it, streamed as Server-Sent Events. They are the only routes the gateway sends to AI Processing, which is on the `edge` and `backend` networks.

See [the service README](../../srcs/services/ai-processing/README.md) for setup. Conventions, tokens and errors are in [00_conventions.md](00_conventions.md).

| Kind | Method | Caller path | Service path | Auth | Success | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Frontend | POST | `/api/ai-processing/digest` | `/digest` | Bearer | 200 (stream) | Done |
| Frontend | POST | `/api/ai-processing/digest/chat` | `/digest/chat` | Bearer | 200 (stream) | Done |
| Internal | GET | — | `/health` | None | 200 | Done |

The health route is registered at the application root, without an `/api` prefix.

## The digest and its chat

### How a request is served

1. The gateway applies two limits before forwarding (both answer `429` in plain text, with `Retry-After` in seconds):
   - per session (the `Authorization` header): 6 answers a minute, burst 3; a digest and its questions share the limit;
   - for everyone: at most 2 answers being written at once.
2. AI Processing verifies the user's access token (`shared_auth`).
3. It reads the user's topics: `GET /internal/v1/me/profile` on Personalization, with the user's token (the user's data, ADR-0008). No profile counts as no topics.
4. It reads the topic summaries: `GET /internal/v1/topics` on Content Management, with its service token (`topics:read` only).
5. It keeps the followed topics that have a summary, in the profile's order, and sends them to the LLM with the request. Without any, it streams a fixed message instead and does not call the LLM.
6. It streams the LLM's answer as it is written.

Errors in steps 2 to 4 are ordinary JSON errors, before the stream. Once the stream has started (`200`), a failure is an `error` event.

### The stream

`Content-Type: text/event-stream`, `Cache-Control: no-store`. Each event is two lines and a blank line; `data` is one line of JSON:

```text
event: chunk
data: {"text": str}          the next piece of the answer; join them in order

event: done
data: {}                     the answer is complete (last event)

event: error
data: {"error": {"code": str, "message": str}}   the answer stopped (last event)
```

| `error` event code | When |
| --- | --- |
| `SERVICE_UNAVAILABLE` | The LLM is unreachable, too slow (`OLLAMA_TIMEOUT_SECONDS` between two pieces), or failed mid-answer |
| `INTERNAL_SERVER_ERROR` | Anything else (logged on the server, no detail sent) |

Closing the connection (the user presses Stop or leaves) stops the LLM.

### Input rules

Checked by the API (and repeated by the frontend). Every body is strict: an unknown field is a `422`.

| Field | Rule |
| --- | --- |
| `length` | `"short"` (default) or `"detailed"` |
| `focus` | Optional, 0 to 200 characters once trimmed; one line, without `<`, `>` or control characters |
| `messages` | 2 to 10 items; the first is the digest (`assistant`), then `user` and `assistant` in turn; the last is a `user` question |
| `messages[].role` | `"assistant"` or `"user"` |
| `messages[].content` | `user`: 1 to 500 characters, one line, without `<`, `>` or control characters. `assistant`: 1 to 4,000 characters, no control characters except the newline |

The server keeps no conversation: the browser sends it with each question. Earlier answers are treated as untrusted input like the rest (see ADR-0011, "Prompt injection").

### POST /api/ai-processing/digest

Service path: `POST /digest`. Writes one digest of today's summaries of the user's topics.

```text
Header: Authorization: Bearer <access token>
Body:
{
  "length": "short" | "detailed",      optional, default "short"
  "focus": str                         optional, default ""
}

200 OK                text/event-stream (see "The stream")
401 Unauthorized      INVALID_TOKEN, TOKEN_EXPIRED (also passed through from Personalization)
422 Unprocessable     VALIDATION_ERROR
429 Too Many Requests (gateway, plain text, Retry-After)
502 Bad Gateway       DOWNSTREAM_ERROR (Personalization answered an unexpected error)
503 Unavailable       SERVICE_UNAVAILABLE (Personalization or Content Management unreachable)
```

Without followed topics, the stream is one `chunk` with "Follow some topics first: ..." then `done`; without any summary yet, one `chunk` with "Your topics have no summary yet today. ..." then `done`.

### POST /api/ai-processing/digest/chat

Service path: `POST /digest/chat`. Answers the last question of the conversation, about today's summaries of the user's topics.

```text
Header: Authorization: Bearer <access token>
Body:
{
  "messages": [
    {"role": "assistant", "content": str},   the digest
    {"role": "user", "content": str},        a question
    ...                                      answers and questions in turn
    {"role": "user", "content": str}         the new question
  ]
}

Responses: as POST /api/ai-processing/digest.
```

## The summary worker

| Command | What it does | Calls | Status |
| --- | --- | --- | --- |
| `summarize` (e.g. `make summarize`) | Assesses missing articles, then summarizes each topic from up to 25 returned articles | `GET /internal/v1/articles?summary=missing&limit=25` (default batch size), `GET /internal/v1/topics`, one `GET /internal/v1/articles?topic_id=...&limit=25` per topic, `PUT .../summary` on Content Management | Done |
| `embed` (later) | Stores article embeddings in its own pgvector database | `GET /internal/v1/articles...` on Content Management | To do |

The article loop uses `ARTICLE_BATCH_SIZE` (default 25) as the request limit and
uses no cursor. It fetches the next batch only after writing an assessment for
every article in the current batch. An empty response ends the article phase.
If summary generation fails, the worker stores a rejected assessment with a
null summary and continues with the next article. Content Management read or
write failures still stop the worker. The topic phase starts after the article
phase finishes.
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
If generation fails for one group, the worker PUTs the latest successfully
generated summary for that topic and continues with the next topic. If the
first group fails, it uses the first article summary as a fallback.

Its pgvector database is provisioned for future working data such as embeddings;
the current worker does not use it or store summaries locally.
