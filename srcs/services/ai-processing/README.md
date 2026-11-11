# AI Processing

AI Processing reads articles from Content Management, generates summaries with
Ollama, and writes them back to Content Management. Its HTTP API exposes only
`/health`. The worker sends each article's summary, rejection flag, and quality
comment through one `PUT`, then builds each topic summary from up to 25 eligible
articles returned by Content Management. The article phase finishes before the
topic phase. Topics with no eligible articles receive an empty-topic summary.
Content Management still needs the topic summary write route for a live run
that reaches a non-empty topic.
The API contract and service ownership are in
[`docs/api/04_content-management.md`](../../../docs/api/04_content-management.md).

## Run the summary worker

For this QEMU VM, `.env.example` sets
`OLLAMA_BASE_URL=http://10.0.2.2:11434`; the worker defaults to
`http://content-management:8000` for Content Management. Set
`CONTENT_MANAGEMENT_BASE_URL` only when running outside Compose.
`OLLAMA_TIMEOUT_SECONDS` defaults to 120.
`OLLAMA_CONTEXT_LENGTH` defaults to 8192 tokens and is sent as `num_ctx` on every
article and topic request, so the worker does not depend on the host's default.
`ARTICLE_BATCH_SIZE` defaults to 25 and controls the `limit` sent when the
worker fetches articles missing summaries. Content Management currently accepts
limits of 1–25, so keep this value in that range. Set it in the service's
`.env` to change the worker batch size.
After four failed generation attempts, the worker saves the article as rejected
with no summary and the comment `AI assessment failed after 4 attempts.` It then
continues to later batches and topic summaries. Generation failures still count
in worker metrics. A failure to save an assessment still stops the run.
If an existing `.env` has `CONTENT_MANAGEMENT_BASE_URL=` with an empty value,
remove that line so the default applies. Update `OLLAMA_BASE_URL` in that file
too; changing `.env.example` does not change an existing `.env`.

From the repository root on the host, run `make summarize` after starting the
stack. It connects to the VM over SSH and executes the worker in the running AI
Processing container. To run the worker from a shell already inside the AI
Processing container, use:

```sh
python -m src.worker
```

The service image does not contain the repository's shared Makefile. When
running the command on the host, override `CONTENT_MANAGEMENT_BASE_URL` and
`OLLAMA_BASE_URL` with addresses reachable from the host, such as
`http://localhost:8083` and `http://localhost:11434`.
An empty missing-article response ends the article phase and starts the topic
phase. If article summary generation fails, the worker saves a rejected
assessment and continues. If a topic group fails, it saves the latest
successfully generated summary for that topic and continues; when the first
group fails, it uses the first article summary. Content Management read or write
failures still stop the worker. There is no retry counter. On another run,
articles with a stored assessment are skipped, including rejected articles.
Topic summaries are recomputed on each run. The worker does not log article text
or tokens. It logs Ollama's completion reason and generated-token count. A
non-stop completion or an accepted summary without sentence-ending punctuation
counts as a generation failure, so the article is stored as rejected.

## Service token

The worker calls Content Management with a service token from Identity
(ADR-0008), with `topics:read`, `articles:read` and `summaries:write`. It needs:

| Setting | Description | Example |
| --- | --- | --- |
| `IDENTITY_URL` | Base URL of Identity, which gives the token | `http://localhost:8081` (host), `http://identity:8000` (containers, set by `compose.yaml`) |
| `ai_processing_client_secret` (secret file) | This service's client secret at Identity, created by `make secrets` | `shared/secrets/services/ai_processing_client_secret` (host), `/run/secrets/ai_processing_client_secret` (containers) |

## Test the local Ollama API

Install and start [Ollama](https://docs.ollama.com/quickstart), then pull a
small local model (or substitute a model that fits your machine):

```sh
ollama pull gemma2:2b
```

Send a short sample article to Ollama's native `POST /api/chat` endpoint to
check the model and local connection:

```sh
curl --fail-with-body --show-error --max-time 120 \
  http://localhost:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gemma2:2b",
    "messages": [
      {
        "role": "system",
        "content": "Summarize the article accurately in its original language. Use two concise sentences. Do not add facts."
      },
      {
        "role": "user",
        "content": "Title: City opens a new library. Language: English. Article: The city opened a library on Monday. It has a reading room and free computer access."
      }
    ],
    "stream": false
  }'
```

This smoke test uses a single response. Check that `done` is `true` and
`message.content` contains a non-empty, accurate summary. The worker uses a
different request: it streams `/api/chat` responses with a JSON schema,
assesses article completeness, and requires `rejected`, `quality_comment`, and
`summary` in the generated JSON. It validates the result before writing it to
Content Management. Local Ollama requests do not need an API key. See the official
[chat endpoint](https://docs.ollama.com/api/chat) and
[local API base URL](https://docs.ollama.com/api/introduction).

The Ollama adapter sends the article's `title`, full `content`, and `language`
in the prompt. For topics, it combines article summaries in groups of up to
four, repeatedly, until one summary remains. Its model name, base URL, and
timeout come from the worker's environment settings.

## Try one article with fake Content Management

Start Ollama on the host with `make ollama`, which uses `OLLAMA_MODEL` from
`srcs/services/ai-processing/.env`. From the repository root on the
host, use the existing Make target to start AI Processing and its dependencies
inside the VM:

```sh
make vm-service SERVICE=ai-processing
```

Then enter the VM with `make connect-vm`. From the repository root inside the
VM, run the one-article test in a temporary AI Processing container:

```sh
docker compose -f compose.yaml -f compose.override.yaml --profile backend --profile databases run --rm --no-deps ai-processing python -m scripts.try_ollama_workflow
```

The temporary container uses the image built by `make vm-service` and skips database
startup because this test has no database dependency. This also works if the
regular AI Processing prestart step fails.

The AI Processing container connects to the host's Ollama at
`http://10.0.2.2:11434`. Use `--ollama-url` if your host uses another reachable
address. The command runs the real worker and Ollama adapter. An in-memory HTTP
mock supplies one article, accepts the assessment write, and serves the saved
summary for the topic phase.
It does not call a live Content Management service.
The command prints the quality comment and saved summaries. With one accepted
article, the topic summary is the same text, so this run makes one Ollama
generation request.

To run the same workflow as an explicit pytest integration test from the VM's
repository root, use:

```sh
docker compose -f compose.yaml -f compose.override.yaml --profile backend --profile databases run --rm --no-deps ai-processing pytest -q -s manual_tests/test_ollama_workflow.py
```

This test lives outside pytest's default `tests/` path. Its article is a
paraphrased, longer test version of OpenAI's [May 13, 2024 GPT-4o announcement](https://openai.com/index/gpt-4o-and-more-tools-to-chatgpt-free/),
with details from the related [model announcement](https://openai.com/index/hello-gpt-4o/).
The test prints the source, article summary, and elapsed wall time. The time
includes model startup or warm-up when needed, so one run is not a reliable
estimate for a larger batch.

To exercise article paging and rejection, run the six-article manual test from
the VM's repository root:

```sh
docker compose -f compose.yaml -f compose.override.yaml --profile backend --profile databases exec -T ai-processing pytest -q -s manual_tests/test_ollama_batch.py
```

The fake Content Management client has five incomplete articles followed by
the complete OpenAI article. The worker requests missing articles with
`limit=5`, so the fake returns pages of five, one, then zero. The test checks
that the incomplete articles are rejected without summaries, the complete
article is accepted, and its summary is written for the topic. It prints the
total elapsed time. No test database is used.

When AI Processing runs in Docker, `localhost` refers to its container, not
the host running Ollama. With this repository's QEMU VM, test host access from
the running container before wiring the adapter:

```sh
docker compose exec ai-processing python -c 'import urllib.request; print(urllib.request.urlopen("http://10.0.2.2:11434/api/tags", timeout=5).status)'
```

An HTTP `200` confirms that the container can reach the host Ollama server.
For that setup, the adapter's base URL is `http://10.0.2.2:11434`; a process
running directly on the host uses `http://localhost:11434`.
