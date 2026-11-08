# Prometheus and Grafana roadmap

## Goal

Monitor the Docker Compose stack with Prometheus and Grafana. Start with a small,
working dashboard for Traefik and one API service, then extend it to the other
services. Keep metrics endpoints internal: the gateway must not route `/metrics`
to users.

**Estimated effort:** 2–4 hours for a local proof of concept; 1–2 working days
for all services, useful dashboards, and basic alerts. These are planning
estimates and assume the Compose stack already starts successfully.

## How the pieces fit

```text
Traefik /metrics ───────┐
FastAPI /metrics ───────┼──> Prometheus ──> Grafana dashboards
Prometheus /metrics ────┘
```

Prometheus *scrapes* HTTP endpoints and stores time series. Grafana queries
Prometheus; it does not collect application metrics itself. Use Docker service
names and container ports in scrape targets, not `localhost` (which would refer
to the Prometheus container).

## Milestone 1 — Get data into Grafana (2–4 hours)

- [ ] Add `prometheus` and `grafana` services to `compose.yaml`, with named data
  volumes and an `observability` Compose profile. Put Prometheus on both `edge`
  and `backend`; put Grafana on the network that contains Prometheus. Pin tested
  image versions rather than using `latest`.
- [ ] Create `srcs/monitoring/prometheus.yml`. Set a 15-second scrape interval
  and scrape `prometheus:9090` first. Give each target a clear `job` name.
- [ ] Enable Traefik's Prometheus exporter in
  `srcs/gateway/traefik.yaml`, using a dedicated internal entry point. Add its
  container address to `prometheus.yml`. Do not publish the metrics port on
  the host or add it to the gateway's public route files.
- [ ] Provision Grafana's Prometheus data source from a file under
  `srcs/monitoring/grafana/provisioning/datasources/`, using
  `http://prometheus:9090` as the URL.
- [ ] For local development, make the Grafana UI reachable on
  `127.0.0.1:3000`. Set an admin password outside version control. Keep this
  local access separate from the public gateway. If running in the project VM,
  arrange VM port forwarding as well.
- [ ] Add the `observability` profile to the relevant Makefile Compose commands
  so `make docker`, `make ps`, `make logs`, and `make down` manage the new
  containers consistently. Document the Grafana address in `README.docker.md`.

**Check:** Prometheus Targets shows its own and Traefik's targets as `UP`;
the `up` query returns `1` for both. In Grafana Explore, select Prometheus and
run `up`. Save a small dashboard with target health and Traefik request rate.

## Milestone 2 — Instrument the APIs (about 3–5 hours)

- [ ] Add a Prometheus Python client or FastAPI instrumentation package to one
  service first, preferably `identity`. Expose `/metrics` from its app factory
  in `src/main.py` and scrape `identity:8000`. Keep `/metrics` off the gateway
  allowlist.
- [ ] Record request count by service, route template, method, and status code;
  record request duration as a histogram. Use route templates such as
  `/accounts/{account_id}`, never raw URLs, user IDs, email addresses, tokens,
  or request bodies as labels.
- [ ] Repeat for `content-management`, `personalization`, and
  `morning-briefing`; add each `service-name:8000` target to Prometheus.
- [ ] Give `ai-processing` worker-specific counters and duration histograms
  for jobs, successes, and failures. Its HTTP request metrics alone will say
  little about the work it performs.
- [ ] Confirm that the existing single-worker Uvicorn setup remains compatible
  with the chosen client. Revisit Prometheus client multiprocess configuration
  if the services later run multiple worker processes.

**Check:** Each target is `UP`; a request through the application changes its
request counter. A failed request changes the appropriate status-code series.
The gateway still returns 404 for an external `/metrics` request.

## Milestone 3 — Make the data useful (about 3–5 hours)

- [ ] Create and provision a dashboard covering service availability, request
  rate, 5xx error rate, and p95 request duration. Add worker job success and
  failure panels for AI Processing.
- [ ] Add a small set of alerts: target down for several minutes, sustained
  elevated 5xx rate, and repeated worker failures. Choose thresholds after
  observing normal traffic; test that each alert can fire and resolve.
- [ ] Decide on Prometheus retention and volume size for the deployment.
  Document how to inspect targets, query metrics, restart the stack, and keep
  Grafana access restricted in shared environments.
- [ ] Validate the merged Compose configuration and Prometheus configuration,
  then perform a smoke test after a restart to confirm data and dashboards
  persist in their named volumes.

**Done when:** a teammate can start the stack, open Grafana, identify a down
service or a rise in errors, and trace the signal to a named Compose service.

## Fastest learning path (about 2–3 hours alongside milestone 1)

1. Follow [Prometheus Getting Started](https://prometheus.io/docs/prometheus/latest/getting_started/)
   through scraping a target. Learn `target`, `job`, `label`, `counter`, and
   `histogram` by looking at the project's own metrics.
2. In Prometheus, try `up`, then `rate(<request_counter>[5m])`. Inspect a
   target's raw `/metrics` response when a series is confusing.
3. Follow [Grafana's Prometheus dashboard guide](https://grafana.com/docs/grafana/latest/fundamentals/getting-started/first-dashboards/get-started-grafana-prometheus/)
   and build two panels from the project's data. Learn Explore before spending
   time on dashboard styling.
4. Read the [Python Prometheus client's FastAPI example](https://prometheus.github.io/client_python/exporting/http/fastapi-gunicorn/)
   when starting milestone 2.

## Project touchpoints

- `compose.yaml` and `compose.override.yaml`: services, networks, volumes,
  local Grafana port.
- `srcs/gateway/traefik.yaml`: internal Traefik metrics entry point.
- `srcs/gateway/dynamic/`: public route allowlist; do not add `/metrics`.
- `srcs/services/*/src/main.py`: FastAPI app factories to instrument.
- `Makefile`, `.env.example`, and `README.docker.md`: developer commands and
  access instructions.
