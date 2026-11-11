# Monitoring stack

This directory holds Prometheus scrape configuration and Grafana provisioning.
The stack runs under the Compose `observability` profile. For startup, VM
access, and troubleshooting commands, see [README.docker.md](../../README.docker.md#observability-in-development).

## How data moves

```text
Traefik :9092/metrics ──────────┐
Five FastAPI apps :8000/metrics ├──> Prometheus ──> Grafana
Prometheus :9090/metrics ───────┤     (15-second scrapes)   (queries, dashboards, alerts)
AI summary worker ──> Pushgateway :9091/metrics ──┘
```

Prometheus scrapes numeric time series from the targets in
[`prometheus.yml`](prometheus.yml). The jobs are `prometheus`, `traefik`,
`pushgateway`, `identity`, `content-management`, `personalization`,
`morning-briefing`, and `ai-processing`. All use container addresses. The
five API jobs scrape `/metrics` on port 8000. Traefik exposes its metrics on
an internal entry point at port 9092; Prometheus reaches it over the `edge`
network and reaches APIs and Pushgateway over `backend`.

The summary worker is a separate, short-lived process. At the end of a run it
pushes last-run gauges to Pushgateway using the fixed job
`ai_processing_summary`; the next run replaces those values. Prometheus then
scrapes Pushgateway. The worker's gauges do not describe traffic to the AI
Processing HTTP API, and `up{job="pushgateway"} == 1` proves only that the
gateway can be scraped. Use `ai_worker_last_run_success` to check the worker
result and service logs for error details.

Grafana's provisioned Prometheus data source points to
`http://prometheus:9090`. Dashboard JSON files live in [`grafana/dashboards`](grafana/dashboards),
and the provisioned alert rules live in
[`grafana/provisioning/alerting`](grafana/provisioning/alerting). The current
rules cover an API target down, an elevated API 5xx rate, and a failed last
worker run. There is currently no overdue-worker alert; the summary worker
is run manually with `make summarize` in the VM.

Compose keeps Prometheus, Pushgateway, and `/metrics` internal. Only Grafana's
UI is bound to the development host, normally at `127.0.0.1:3000`; the VM
forwards that development port. Do not route metrics through public Traefik
routes or expose their ports on the host. Grafana's admin password comes from
`shared/secrets/grafana_admin_password`, outside version control. Prometheus
keeps data for at most 15 days or 2 GB, whichever limit is reached first;
allow at least 3 GB for its volume because recent data and the write-ahead
log can temporarily exceed that limit. Named volumes hold Prometheus data,
Grafana data, and Pushgateway's persisted latest values.

## Prometheus–Grafana metric contract

Dashboards and alerts must query the names and labels exported by the code,
rather than infer them from HTTP status or logs. A **counter** increases until
its process restarts, so use `rate()` for per-second traffic. A **gauge** holds
the latest value. A **histogram** provides `_bucket`, `_sum`, and `_count`
series; use its buckets for percentiles.

### FastAPI HTTP traffic

All five APIs use `prometheus-fastapi-instrumentator` with explicitly
configured request and latency metrics:

| Metric | Type and meaning | Labels |
| --- | --- | --- |
| `http_requests_total` | Counter of completed responses, including handled 5xx responses | `service`, `handler`, `method`, `status` |
| `http_request_duration_seconds` | Histogram of completed request durations in seconds | `service`, `handler`, `method` |

`service` is one of the five fixed API Compose names listed above. `handler`
is a route template such as `/accounts/{account_id}`; unmatched paths are
grouped as `none`. `method` is the HTTP method, and `status` is the exact
response code, such as `200` or `503`. `/metrics` is excluded from HTTP
instrumentation, so scrapes do not inflate request counts. Never add raw
paths, article or topic IDs, user IDs, emails, tokens, request bodies, or
exception messages as labels. HTTP metrics count responses; exception
tracebacks remain in service logs.

### AI summary worker

These gauges have no metric labels. Pushgateway attaches its stable
`job="ai_processing_summary"` grouping to the scraped series.

| Metric | Meaning |
| --- | --- |
| `ai_worker_last_completion_timestamp_seconds` | Unix time of the last finished run, including a failed run |
| `ai_worker_last_run_success` | `1` if the run had no item or fatal failures; otherwise `0` |
| `ai_worker_last_run_duration_seconds` | Duration of the last run, in seconds |
| `ai_worker_last_run_article_failures` | Article generation failures in the last run |
| `ai_worker_last_run_topic_failures` | Topic group generation failures in the last run |

These are last-run values, not cumulative counters or a history of runs.
A normal content rejection is not an article generation failure. A handled
article or topic failure is reflected in the gauge published at the end of
the run; a fatal error is recorded and then raised. A failed push is logged.
The gauges are absent until the first successful push.

### Content Management ingestion

These metrics come from the long-running Content Management API process:

| Metric | Type and meaning | Labels |
| --- | --- | --- |
| `content_ingestion_runs_total` | Counter of completed ingestion runs | `outcome`: `succeeded`, `partial`, or `failed` |
| `content_ingestion_articles_created_total` | Counter of articles stored during ingestion | none |
| `content_ingestion_failures_total` | Counter of reported source discovery and article processing failures | none |
| `content_ingestion_last_completion_timestamp_seconds` | Gauge with Unix time of the last completed run, including failure | none |

`POST /internal/v1/ingestion-runs` can return `201` for both full and partial
success, so its HTTP status alone cannot distinguish those outcomes. An
already-running `409` is still an HTTP response but not a completed ingestion
run. These in-process metric values reset when the API restarts; Prometheus
retains earlier samples. Keep source IDs, article IDs, and error messages out
of labels.

## Verify the contract

After starting the stack with `make docker`, open Grafana Explore and select
the provisioned Prometheus data source. Useful starting queries are:

```promql
up
sum by (service) (rate(http_requests_total[5m]))
sum by (service) (rate(http_requests_total{status=~"5.."}[5m]))
histogram_quantile(0.95, sum by (service, le) (rate(http_request_duration_seconds_bucket[5m])))
ai_worker_last_run_success
```

`up` is `1` for a scrapeable target and `0` for a failed scrape. A missing
HTTP rate or 5xx series may mean no matching requests have occurred yet;
the worker series is absent before its first push. Inspect raw metrics and
Prometheus Targets from inside the Compose network using the commands in
`README.docker.md`. Generate an API request and confirm its counter changes;
run the worker and confirm its last-run gauges change. Check the relevant
service logs when a metric indicates a failure.

The provisioning files describe intended dashboards and alerts. Verify that
Grafana actually loads them, and test alert firing and resolution before
treating those features as operational.
