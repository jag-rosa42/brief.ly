# Prometheus and Grafana roadmap — two people

## Goal

Monitor the Compose stack with Prometheus and Grafana: availability, HTTP
traffic, errors, latency, and AI summary worker outcomes. Keep `/metrics`,
Prometheus, and Pushgateway internal. The public Traefik routes must never
forward metrics endpoints.

Estimated effort, assuming the stack already starts: **Person 1: 8–12 hours;
Person 2: 9–13 hours.** These are estimates; check progress after the first
working metrics appear.

```text
Traefik /metrics ───────────────┐
FastAPI /metrics (five APIs) ───┼──> Prometheus ──> Grafana
Prometheus /metrics ────────────┤
AI worker ──> Pushgateway ──────┘
```

Prometheus scrapes numeric metrics, not logger output. HTTP metrics count
responses, including 5xx responses. `make summarize` runs a separate,
short-lived process inside the AI Processing container; its handled failures
need explicit metrics and a Pushgateway export. Logs keep the traceback.

## Start together: agree on the metric contract (15–30 minutes)

- [x] Choose one Prometheus Python client or FastAPI instrumentation package.
  Record its actual HTTP request counter, duration histogram, and labels.
  Dashboards and alerts must use those names, not guessed names.
- [x] Agree that HTTP labels use bounded values only: service, route template,
  method, and status. Never use raw paths, article or topic IDs, user IDs,
  emails, tokens, request bodies, or exception messages.
- [x] Review the batch worker's last-run gauges and stable Pushgateway job
  grouping in the contract below. A short-lived process must not publish
  resetting per-run counters as cumulative totals.
- [x] Exchange the final metric names and file paths as each piece lands.
  Both people can start their own files immediately.

### Agreed metric contract

#### FastAPI HTTP requests

Use [`prometheus-fastapi-instrumentator`](https://github.com/trallnag/prometheus-fastapi-instrumentator)
for all five FastAPI apps. Configure its `metrics.requests` and
`metrics.latency` functions explicitly so the exported metrics have the
following names and labels:

| Metric | Type and meaning | Labels |
| --- | --- | --- |
| `http_requests_total` | Counter of completed HTTP responses, including handled 5xx responses | `service`, `handler`, `method`, `status` |
| `http_request_duration_seconds` | Histogram of completed HTTP request durations in seconds; exports `_bucket`, `_sum`, and `_count` series | `service`, `handler`, `method` |

Set `service` to one of the five fixed Compose service names. `handler` is the
FastAPI route template, such as `/accounts/{account_id}`; group unmatched
paths under the fixed value `none`. `method` is the HTTP method. Configure
`should_group_status_codes=False`, so `status` is the exact response code
(for example, `200` or `503`), not a `2xx` or `5xx` group. Exclude `/metrics`
from HTTP instrumentation. Do not attach request-specific or sensitive values
to any metric. Keep `/metrics` accessible only on the internal network.

AI Processing configures these HTTP metrics in
`srcs/services/ai-processing/src/infrastructure/metrics/http.py`. Its fixed
`service="ai-processing"` label is supplied to the instrumentator's
per-request info before the request counter and duration histogram run,
because the installed instrumentator does not populate that custom label
itself. The worker metrics below use a separate process and registry.

#### AI summary worker

Use these last-run gauges for the separate, short-lived summary process:

| Metric | Type and meaning | Labels |
| --- | --- | --- |
| `ai_worker_last_completion_timestamp_seconds` | Gauge: Unix time of last finished run, including failure | none |
| `ai_worker_last_run_success` | Gauge: `1` only if the run completed without item or fatal failures; otherwise `0` | none |
| `ai_worker_last_run_duration_seconds` | Gauge: duration of last run in seconds | none |
| `ai_worker_last_run_article_failures` | Gauge: article generation failures in last run | none |
| `ai_worker_last_run_topic_failures` | Gauge: topic group generation failures in last run | none |

Push them with the stable Pushgateway job `ai_processing_summary`, without a
run ID or other run-specific grouping label. A new run replaces the previous
values for that job. Do not publish resetting per-run counters as cumulative
totals; persist cumulative counts outside the worker if they are needed
later. These gauges represent the batch result, not AI Processing's HTTP
traffic.

#### Content Management ingestion

Content Management ingestion needs separate outcome metrics because its
`POST /internal/v1/ingestion-runs` returns `201` for both full and partial
success. Add these to the Content Management API process:

| Metric | Type and meaning | Labels |
| --- | --- | --- |
| `content_ingestion_runs_total` | Counter of completed ingestion runs | `outcome`, one of `succeeded`, `partial`, or `failed` |
| `content_ingestion_articles_created_total` | Counter of articles stored during ingestion | none |
| `content_ingestion_failures_total` | Counter of source discovery and article processing failures reported by ingestion | none |
| `content_ingestion_last_completion_timestamp_seconds` | Gauge containing the Unix time of the last completed ingestion run, including failure | none |

Record `failed` when a run returns a failed result or raises an unexpected
error, and preserve the existing error response or exception behavior. A
`409` for an already-running ingestion is not a completed run; its HTTP
response is still counted by `http_requests_total`. These metrics live in
the long-running API process, so their current values reset or disappear
when that process restarts; Prometheus retains its earlier samples. Do not
use source IDs, article IDs, or error messages as labels.

Verify these names, labels, and 5xx behavior against the real `/metrics`
output before building dashboards or checking off the contract items.

## Person 1 — Prometheus, Traefik, AI worker, and ingestion metrics

**File ownership:** `compose.yaml`, `compose.override.yaml`,
`compose.mac.yaml` if needed, `srcs/monitoring/prometheus.yml`,
`srcs/gateway/traefik.yaml`, `srcs/services/ai-processing/`, `Makefile`,
`.env.example`, VM forwarding scripts, and these Content Management files:
`pyproject.toml`, `uv.lock`, `src/api/routers/ingestion_runs/`, a new
`src/infrastructure/metrics/` module, `tests/unit/api/test_ingestion_runs.py`,
and new ingestion-specific tests. Person 2 owns the rest of Content
Management, the other three APIs, and Grafana provisioning files. Do not
edit a shared file at the same time; Person 1 adds both the HTTP
instrumentator and Prometheus Python client dependencies to Content
Management's dependency files before Person 2 instruments its HTTP app.

### P1.1 — Bring up the monitoring infrastructure

- [x] Add pinned Prometheus, Grafana, and Pushgateway images to `compose.yaml`
  under an `observability` profile. Give Prometheus and Grafana named volumes.
  If the latest worker result must survive a Pushgateway restart, configure
  its persistence file on a named volume.
- [x] Put Prometheus on `edge` and `backend`; put Grafana and Pushgateway on
  `backend`. Prometheus must reach Traefik on `edge` and APIs on `backend`.
  Do not publish Prometheus, Pushgateway, or Traefik metrics ports on the host.
- [x] In the development override, bind Grafana to `127.0.0.1:3000`, following
  the existing `DEV_BIND_ADDRESS` convention for the VM. Supply its admin
  password outside version control. Mount Person 2's provisioning files.
- [x] If the team uses the project VM, add Grafana's development port to
  `shared/script/create-vm/network.sh` and pass it through `Makefile`'s
  `VM_QEMU_ENV`. Keep production forwarding limited to the gateway unless a
  separate access policy is designed.

**Check:** the merged `docker compose config` renders the services and
networks. Local Grafana opens at `http://127.0.0.1:3000`; the other monitoring
endpoints have no host ports.

### P1.2 — Scrape Prometheus, Traefik, Pushgateway, and APIs

- [x] Create `srcs/monitoring/prometheus.yml` with a 15-second scrape
  interval. Use named jobs for Prometheus, Traefik, Pushgateway, and each of
  `identity`, `content-management`, `personalization`, `morning-briefing`, and
  `ai-processing` at `<service>:8000/metrics`. Use container addresses, not
  `localhost`.
- [x] Enable Traefik's Prometheus exporter in `srcs/gateway/traefik.yaml` on
  a dedicated internal entry point. Scrape it over `edge`. Do not publish the
  port or add it to `srcs/gateway/dynamic/routers.yaml`.
- [x] Validate the config with `promtool` and inspect Prometheus Targets.
  APIs not yet instrumented by Person 2 may be `DOWN` during parallel work;
  all must be `UP` at integration.

**Check:** Prometheus and Traefik targets are `UP`, and `up` returns `1` for
both. Inspect Traefik's raw metrics and query them in Grafana Explore once
Person 2's data source exists.

### P1.3 — Instrument the AI Processing worker

- [x] Add the chosen client to AI Processing's `pyproject.toml` and `uv.lock`.
  Expose ordinary HTTP request metrics from its `src/main.py` app; these
  describe the `/health` API, not the summary worker.
- [ ] In `src/application/SummarizeArticles.py`, record a generation failure
  in the existing exception path. In `src/application/summarize_topics.py`,
  record a topic group failure in its exception path. Keep
  `logger.exception(...)` and current fallback behavior. A normal content
  rejection is not a generation failure.
- [ ] Pass a small, testable metrics recorder to the application code. Do not
  rely on the FastAPI process's in-memory registry: `make summarize` starts a
  separate Python process through `docker compose exec`.
- [ ] In `src/worker.py`, measure the run and push last-run gauges to
  `pushgateway:9091` in a `finally` path, including uncaught failure. Re-raise
  fatal errors after recording. Log a failed metrics push clearly.
- [ ] Test success, a handled article failure, a handled topic failure, and
  fatal failure with the push boundary mocked. Check that labels contain no
  IDs, article text, or exception messages.

**Check:** a failed summary changes a Pushgateway-exposed gauge even after
the worker exits, and its traceback remains in logs. The worker result is
not inferred from AI Processing HTTP request metrics.

### P1.4 — Instrument Content Management ingestion

- [ ] Add `prometheus-fastapi-instrumentator` and `prometheus-client` to
  Content Management's `pyproject.toml` and `uv.lock`; Person 2 uses the
  instrumentator dependency for its HTTP metrics without editing these files.
- [ ] Record the ingestion metrics in the contract from the result of
  `POST /internal/v1/ingestion-runs`. Preserve its current response and
  exception behavior. Do not label metrics with source or article IDs.
- [ ] Test full success, partial `201`, a failed result, and an unexpected
  failure. Check that they update the correct outcome, article and failure
  counts, and completion timestamp. A `409` must not count as a completed run.

**Check:** a partial `201` changes the `partial` outcome series in Content
Management's internal `/metrics`; a failed run changes `failed`, and a `409`
does not change the ingestion run count.

### P1.5 — Make startup and retention reproducible

- [ ] Add `observability` to relevant Makefile Compose profile selections
  for `make docker`, `make ps`, `make logs`, `make down`, and corresponding VM
  and production paths. Keep `make docker SERVICE=<name>` useful without
  forcing unrelated service dependencies.
- [ ] Set a deliberate Prometheus retention period and document its expected
  volume use. Verify the configured Grafana password is not committed.
- [ ] Restart the monitoring stack and verify stored Prometheus data and the
  latest worker result remain available as designed.

**Handoff:** give Person 2 the final scrape job names, Traefik metric names,
worker and ingestion metric names, and a command that produces a visible
worker result. Tell Person 2 when Content Management's dependency files are
ready for HTTP instrumentation.

## Person 2 — Backend HTTP metrics, Grafana, and alerts

**File ownership:** `srcs/services/identity/`,
`srcs/services/content-management/` except the files assigned to Person 1,
`srcs/services/personalization/`, `srcs/services/morning-briefing/`,
`srcs/monitoring/grafana/`, and `README.docker.md`. Read Person 1's Compose
and Prometheus files as needed; send Person 1 the Grafana provisioning paths
for the Compose mounts.

### P2.1 — Instrument one FastAPI app, then repeat

- [ ] Start with `identity`: add the selected package to `pyproject.toml`
  and `uv.lock`, expose internal `/metrics` from the `src/main.py` app
  factory, and record request count and duration histogram.
- [ ] Use route templates such as `/accounts/{account_id}` rather than raw
  paths. Give unmatched paths one fixed label. Label by service, method, and
  response status. Do not expose `/metrics` through Traefik.
- [ ] Verify a handled 500 or 503 response changes the relevant status
  series. The existing shared exception handlers log tracebacks; HTTP metrics
  count their returned responses.
- [ ] Repeat for `content-management`, `personalization`, and
  `morning-briefing`, updating dependency and lock files for
  `personalization` and `morning-briefing`. Person 1 updates Content
  Management's dependency and lock files for both HTTP and ingestion metrics.
  Add focused tests for the distinct HTTP instrumentation behavior. Confirm
  compatibility with the current single-worker Uvicorn setup; revisit
  multiprocess configuration only if the service process model changes.

**Check:** each API exposes internal `/metrics`; a request changes its count,
a failing request changes the status series, and labels contain no
request-specific data. Send the actual metric names to Person 1.

### P2.2 — Provision Grafana and useful dashboards

- [ ] Create a provisioned Prometheus data source under
  `srcs/monitoring/grafana/provisioning/datasources/` with URL
  `http://prometheus:9090`. Add dashboard provisioning and dashboard JSON
  under `srcs/monitoring/grafana/`. Person 1 mounts these files in Compose.
- [ ] Start with Grafana Explore: run `up` and an HTTP request-rate query.
  Build initial panels for target health and Traefik request rate. Inspect
  raw `/metrics` when a series is confusing.
- [ ] Add panels for service availability, request rate, 5xx rate, p95
  duration from histogram buckets, and AI worker last run result, age,
  duration, and article/topic failure counts. Use actual metric names and
  show the Compose service in legends. Handle zero traffic and missing data
  clearly.

**Check:** a fresh Grafana start loads the data source and dashboard without
manual setup. A request and a worker run change their respective panels.

### P2.3 — Alert and document

- [ ] Provision a small alert set: an API target down for several minutes,
  sustained elevated 5xx rate, a failed worker run or high last-run item
  failure count, and a worker completion older than its expected interval.
  Observe normal traffic before choosing numeric thresholds. Pushgateway `UP` only proves
  the gateway is reachable, not that the batch job succeeded.
- [ ] Test each alert firing and resolving. The worker currently runs by
  manual `make summarize`; agree on a real run cadence before enabling an
  overdue-run alert.
- [ ] Document in `README.docker.md` how to start and stop observability,
  access Grafana locally and from the VM, inspect Targets and raw metrics,
  run sample queries, find exception tracebacks in logs, and restrict
  Grafana access in shared environments. Confirm VM instructions with
  Person 1 after forwarding is implemented.

**Handoff:** give Person 1 the final HTTP metric names and labels and the
Grafana provisioning paths required in Compose.

## Integration and definition of done — both people

- [ ] Validate merged Compose and Prometheus configurations; start the full
  stack. Resolve interface mismatches together.
- [ ] Prometheus Targets shows itself, Traefik, Pushgateway, and all five
  FastAPI targets `UP`. Query `up` and an HTTP request rate in Prometheus
  and Grafana Explore.
- [ ] Make a normal and failing backend request. Verify request and status
  metrics change. Verify an external API `/metrics` path does not return
  metrics through Traefik.
- [ ] Run the AI worker successfully and with a controlled failure. Verify
  handled failures affect last-run gauges even when work continues, while
  an uncaught failure keeps the command failed. Find detail in logs.
- [ ] Verify dashboard panels and alerts, restart the monitoring stack, and
  confirm Prometheus data, provisioned dashboards, and latest worker result
  persist as designed.
- [ ] Each person independently inspects raw `/metrics`, runs `up` and
  `rate(<request_counter>[5m])`, and creates or edits a Grafana panel. Each
  can explain target, job, label, counter, gauge, and histogram using this
  project's data.

**Done when:** a teammate can identify a down service, a rise in API errors,
or a failed AI batch run in Grafana, then find the named Compose service and
relevant logs.

## Learning references

- [Prometheus Getting Started](https://prometheus.io/docs/prometheus/latest/getting_started/)
- [Prometheus batch-job guidance](https://prometheus.io/docs/practices/instrumentation/)
- [Python client Pushgateway example](https://prometheus.github.io/client_python/exporting/pushgateway/)
- [Grafana Prometheus dashboard guide](https://grafana.com/docs/grafana/latest/fundamentals/getting-started/first-dashboards/get-started-grafana-prometheus/)
