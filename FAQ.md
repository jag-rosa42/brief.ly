# Monitoring FAQ

This FAQ explains the ideas we need before adding Prometheus and Grafana to
this project.

## What is a metric?

A metric is a number with a name. For example, `http_requests_total` is a
number that grows by one whenever a FastAPI app finishes an HTTP request.
Labels describe *which* requests the number refers to.

Suppose Identity has answered seven successful health checks. Its `/metrics`
response could contain:

```text
http_requests_total{service="identity",handler="/health",method="GET",status="200"} 7
```

Read this as: "Identity has returned seven `200` responses to `GET /health`"
since this app process started. Another label combination, such as
`status="503"`, has its own count. A counter can reset when the process
restarts; Prometheus understands counter resets when calculating a rate.

## What is a metric contract?

It is an agreement between the people adding metrics and the people making
dashboards. For each metric, we agree on its **name**, **type**, **meaning**,
and **labels**. For example:

| Part | Our proposed HTTP request metric |
| --- | --- |
| Name | `http_requests_total` |
| Type | Counter |
| Meaning | Number of completed HTTP responses |
| Labels | `service`, `handler`, `method`, `status` |

The name is like a field name in an API: both sides must use the same one. If
FastAPI publishes `http_requests_total` but Grafana asks Prometheus for
`api_requests_total`, the graph will have no data. The contract also says what
each label means, so we do not accidentally mix raw URLs with route templates.
The chosen contract is recorded in `roadmap.md` below the first roadmap step.

## Does Prometheus ask FastAPI for `http_requests_total`?

No. Prometheus asks each FastAPI service for its entire metrics page, for
example:

```text
GET http://identity:8000/metrics
```

That page contains **all** metrics registered in the app, including
`http_requests_total`. Prometheus fetches the page regularly (our roadmap
proposes every 15 seconds) and stores each value with the time it was fetched.
Grafana then asks **Prometheus** for a named metric when drawing a graph.

```text
Request → FastAPI updates numbers → /metrics shows current numbers
        → Prometheus fetches and stores them → Grafana queries Prometheus
```

`/metrics` is for internal monitoring traffic. Traefik must not make it a
public API route.

## How can I check whether Prometheus is scraping targets?

Run this from the host while the project VM is running:

```bash
ssh -p "${VM_SSH_PORT:-2222}" "$(id -un)@127.0.0.1" \
  'docker exec prometheus promtool query instant http://localhost:9090 up'
```

`docker exec` runs `promtool` inside the Prometheus container, where
`localhost:9090` is the Prometheus server. `promtool query instant` asks for
the current value of the PromQL expression `up`. Prometheus creates one `up`
series for each configured scrape target. For example:

```text
up{instance="gateway:9092", job="traefik"} => 1
```

`job` identifies the scrape job, and `instance` is its target address. A value
of `1` means the latest `/metrics` scrape succeeded; `0` means it failed. A
missing or unimplemented `/metrics` endpoint can produce `0`. This checks
whether Prometheus can collect metrics, not whether the whole application is
healthy.

## What is FastAPI instrumentation, and how does it record requests?

Instrumentation is code that watches the app while it works. A FastAPI
instrumentation library installs **middleware**: code that runs around each
request. It starts a timer, lets FastAPI handle the request, reads the response
status, increases a counter by one, and records how long the request took.
These numbers stay in the running FastAPI process until Prometheus fetches
them from `/metrics`.

We configure the library once in each app. We do **not** add counting code to
every route, and FastAPI does not send each individual request to Prometheus.
The setup takes a few calls because we need to choose labels, status-code
behavior, and the `/metrics` endpoint. We will check the real `/metrics`
output before writing Grafana queries.

## Why do labels use route templates rather than the URL requested?

If someone requests `/accounts/123`, the `handler` label should be
`/accounts/{account_id}`. That lets all requests for the same route share a
series. Using `/accounts/123`, `/accounts/456`, and so on would create many
series and could expose account IDs. We also keep article IDs, user IDs,
emails, tokens, request bodies, and exception messages out of labels.

## Is the AI summary worker measured the same way?

No. The worker runs as a separate, short-lived process, so FastAPI's HTTP
instrumentation only measures the API, not the summary job. The worker will
record the result of its **last run** and send those gauges to Pushgateway.
Prometheus will scrape Pushgateway. Logs will still hold the details of any
failure.

## What contract did we choose for this project?

All five FastAPI apps will use
[`prometheus-fastapi-instrumentator`](https://github.com/trallnag/prometheus-fastapi-instrumentator).
We will configure these two HTTP metrics:

| Name | What its number means | Labels |
| --- | --- | --- |
| `http_requests_total` | Count of completed responses, including errors | `service`, `handler`, `method`, `status` |
| `http_request_duration_seconds` | How long completed requests took, recorded in histogram buckets | `service`, `handler`, `method` |

The `service` label is one of our five fixed Compose service names. The
`handler` label is a route template, such as `/accounts/{account_id}`; an
unmatched route gets the fixed value `none`. The `status` label is the exact
response code, such as `200` or `503`. The duration histogram produces
`http_request_duration_seconds_bucket`, `_sum`, and `_count` series, which
Prometheus can use for latency graphs. We will not count scrapes of `/metrics`
as application requests.

The separate AI worker will publish these last-run gauges:

| Name | What its value means |
| --- | --- |
| `ai_worker_last_completion_timestamp_seconds` | Unix time when the last run finished, including failure |
| `ai_worker_last_run_success` | `1` if the run had no item or fatal failures; otherwise `0` |
| `ai_worker_last_run_duration_seconds` | How long the last run took, in seconds |
| `ai_worker_last_run_article_failures` | Article generation failures in the last run |
| `ai_worker_last_run_topic_failures` | Topic group generation failures in the last run |

It will use the fixed Pushgateway job `ai_processing_summary`, rather than
a new job name for every run. The [roadmap](roadmap.md#agreed-metric-contract)
is the source of truth for the contract.

Content Management ingestion needs its own metrics. A partial run can return
HTTP `201`, just like a fully successful run, so the HTTP request counter
alone cannot tell them apart:

| Name | What its value means | Labels |
| --- | --- | --- |
| `content_ingestion_runs_total` | Number of completed runs for each outcome | `outcome`: `succeeded`, `partial`, or `failed` |
| `content_ingestion_articles_created_total` | Number of articles stored by ingestion | none |
| `content_ingestion_failures_total` | Number of source discovery and article processing failures | none |
| `content_ingestion_last_completion_timestamp_seconds` | Unix time when the last ingestion run finished | none |

The `outcome` label has only those three fixed values. An HTTP `409` means
another ingestion is already running, so it does not count as a completed
run. These metrics are held by the Content Management API process: their
current values reset or disappear after it restarts, while Prometheus keeps
older samples.

This is the **chosen design**. We still need to confirm the names and labels
in the running apps' `/metrics` output before considering implementation done.

## P1.3 questions: AI Processing dependencies and HTTP metrics

### What do `pyproject.toml` and `uv.lock` do?

`pyproject.toml` lists the Python packages AI Processing needs. `uv.lock`
records the exact resolved versions and their dependencies, so teammates and
containers install the same set. Add a dependency to `pyproject.toml`, then
run `uv lock`; do not edit the lock file by hand.

### Why add both Prometheus packages?

`prometheus-fastapi-instrumentator` measures requests to the FastAPI app.
`prometheus-client` creates metrics and lets the separate summary worker send
its last-run result to Pushgateway. The instrumentator also uses the client
internally.

### What are counters, gauges, and histograms?

A **counter** counts events and only increases while its process runs, such as
`http_requests_total`. A **gauge** holds a value that can rise or fall, such
as `ai_worker_last_run_success` (`1` or `0`). A **histogram** counts observations
in buckets and also exports their count and sum. We use it for HTTP request
durations. The summary worker starts a new process for each run, so it
publishes last-run gauges instead of a resetting per-run counter.

### Why configure status and unmatched-path grouping?

`should_group_status_codes=False` keeps exact codes such as `200` and `503`
instead of broad groups such as `2xx` and `5xx`. With
`should_group_untemplated=True`, a request that matches no route gets the
fixed `handler="none"` label. This avoids putting arbitrary requested paths
in metric labels.

### What do `metrics.requests(...)` and `metrics.latency(...)` add?

`metrics.requests(...)` adds the completed-request counter.
`metrics.latency(...)` adds the duration histogram. The histogram uses
`should_include_status=False` because our contract gives it only `service`,
`handler`, and `method` labels. Both functions use the fixed
`service="ai-processing"` label to identify this API. `/metrics` is excluded
so Prometheus scrapes do not count as application requests.

### Why does the service label need an adapter?

In the installed instrumentator version, `custom_labels` declares the
`service` label, but the metric functions then try to read `service` from the
per-request info object without setting it there. The small adapter in
`src/infrastructure/metrics/http.py` supplies the fixed value before those
functions run. Without it, a request raises `AttributeError` instead of
recording metrics. The label never contains a user ID, article text, or
request-specific value.

## What should we read to understand the metric contract?

Read these in order. You do not need to read the whole Prometheus manual.

1. [Metric and label naming](https://prometheus.io/docs/practices/naming/):
   Learn why a counter name ends in `_total`, why a duration name ends in
   `_seconds`, and why IDs should not be label values.
2. [Metric types in the Python client](https://prometheus.github.io/client_python/instrumenting/):
   Learn when to use a counter, gauge, or histogram. For this project, HTTP
   response counts are counters, request durations are histograms, and the
   worker's last-run values are gauges.
3. [Prometheus instrumentation practices](https://prometheus.io/docs/practices/instrumentation/):
   Focus on the sections about labels and batch jobs. They explain our
   route-template labels and why the short-lived worker needs special care.
4. [FastAPI instrumentator documentation](https://github.com/trallnag/prometheus-fastapi-instrumentator):
   Check the actual metric names, labels, and configuration supported by the
   chosen library. Grafana queries must match what our apps really export.

For each proposed metric, try to complete this sentence: **"This metric
measures ___, in units of ___; it changes when ___; its labels can only
contain ___."** If we can answer it clearly, a teammate can implement and
query the metric without guessing.

When we build the p95 latency panel, read the [histogram guide](https://prometheus.io/docs/practices/histograms/)
for buckets and percentile queries. That detail is not needed to understand
the contract's basic names and meanings.

---

## Feature 229 decision memo: status, backups, and recovery

This section records the team's choices from the planning discussion. It is a
**plan**, not a claim that the work below has already been implemented. See
the feature 229 `roadmap.md` for ordered tasks and acceptance checks. The FAQ
above comes from `feature/78-infra-implement-prometheus-grafana` and explains
that branch's monitoring concepts.

### Will the status page be in Grafana, React, or FastAPI?

It will be an **internal Grafana view for the team**. We do not need a new
React page or a FastAPI status service. The existing P2.2 Grafana dashboard
can serve as the status page after we add a clear gateway reachability panel.
If that dashboard proves too detailed for a quick check, we can make a small
summary dashboard later.

### What happens to the status page if the application stack is stopped?

Grafana cannot remain available if it is stopped with the same Compose
project. After feature 78 is integrated, we plan to move its **existing**
Grafana, Prometheus, and Pushgateway services into a separate monitoring
Compose project on the same VM. Application-project `down` will then leave
monitoring running. We are changing deployment ownership, not creating a
second Grafana or Prometheus installation.

This protects the status view from an **application Compose outage**. It does
not protect it from a VM, host, or Docker daemon outage. Monitoring would need
another host to remain visible during those failures.

### How can Prometheus scrape services in another Compose project?

Both projects will join shared Docker networks created independently of
either project and declared `external` in Compose. Prometheus can still reach
API targets such as `identity:8000` and Traefik on those networks. Grafana
will continue to reach Prometheus at `http://prometheus:9090`. Internal
`/metrics` routes and Pushgateway must not be published to users.

### What is an HTTP probe, and what does Blackbox Exporter add?

A probe is a repeated check of a target. The existing FastAPI `/health`
checks test a service and its database from inside the stack. Prometheus
Blackbox Exporter will make an HTTP request through the application's HTTPS
gateway and report `probe_success`: `1` when the request works, `0` when it
fails. This checks reachability from outside the application containers, so
it can reveal a gateway failure even when an API's internal health check is
fine. Prometheus scrapes the exporter; Grafana displays the resulting metric.
Prometheus `up` means a metrics target was scraped, which is a different
question from whether the HTTP probe succeeded.

### Does our teammate need to redesign his feature 78 dashboard?

No. He can finish P2.2 through the end of his roadmap as planned, including
dashboard provisioning and alerts. Feature 229 will integrate that work,
then add the gateway probe panel and backup freshness status. The main
integration changes concern Compose, networks, Make commands, and deployment
documentation. Confirm his final metric names and provisioning paths before
editing the dashboard. Avoid simultaneous changes to his Grafana files.

### Should this be orchestrated by Kubernetes instead of Compose?

The project currently deploys on one VM with Compose, so this roadmap keeps
Compose. Kubernetes can manage probes and restarts, but a single-node cluster
would still fail with its VM and would not replace off-VM backups or restore
drills. A multi-node Kubernetes migration is a separate platform decision.

### What are RPO and RTO, and what did we choose?

**RPO** is the maximum acceptable age of restored data. **RTO** is the target
time to restore service. We agreed on daily backups, a **24-hour RPO**, and
a proposed **4-hour RTO**. The four-hour target must be tested with a timed
clean restore; it is not yet a demonstrated guarantee. Companies choose these
targets according to service importance, data-loss tolerance, cost, and the
results of restore drills. There is no one universal company standard.

### Where will backups go, and how can I change the directory?

Set `BACKUP_HOST_DIR` in the root `.env` on the **host** to an absolute path
outside `VM_DIR`. The planned host-side backup command will store encrypted
backup snapshots there. Changing this variable will change the destination
without editing scripts. The command must fail clearly if it is missing or
points inside the VM disk directory. A directory on the host survives loss
of the VM, but not loss of that host's disk.

### Will I be able to demonstrate manual backup and restore?

Yes. The plan requires a manual backup command, a way to list and choose
snapshots, and a manual restore command. The scheduled backup must use the
same logic as the manual command. For evaluation, restore the chosen snapshot
into a separate disposable environment, then query recognizable records in
both the regular PostgreSQL and pgvector databases. Do not overwrite live
application data just to demonstrate recovery.

### How will a VM restore read the host's backup directory?

The **host initiates SSH** using the project's existing host-to-VM connection.
The restore command reads the selected snapshot from `BACKUP_HOST_DIR`, sends
its archives to a clean or disposable VM, runs the database restore there,
and verifies the result. The VM does not need a writable host-directory mount
or an SSH server running on the host. If the original VM has been lost, a new
VM must be provisioned before this transfer and restore can run.

### What remains to decide or prove?

Choose a real host directory with enough space, agree on backup retention and
which secrets must be recoverable, then build and test the commands. Confirm
that scheduled backups can run while the host is awake, that failed or stale
backups alert the team, and that a clean restore meets the agreed targets.
