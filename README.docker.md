# Container environments

This guide covers the Docker Compose development and production environments. For running services directly on your machine, see [README.dev.md](README.dev.md).

## Prerequisites and configuration

Install Docker Engine with the Compose plugin (`docker compose`), or use the development VM, which has both ([README.dev.vm.md](README.dev.vm.md)). Then create the shared environment file and service configuration files:

```bash
cp .env.example .env
cp srcs/services/identity/.env.example srcs/services/identity/.env
```

Container targets create `shared/secrets/postgres_password`, the JWT keys and the gateway's certificate (`shared/secrets/certs/`) automatically when they do not exist; do not commit these files. PostgreSQL and pgvector store their data in Docker-managed named volumes.

The production environment loads `compose.yaml`. Development commands also load `compose.override.yaml`; macOS additionally loads `compose.mac.yaml` to enable filesystem polling for the frontend bind mount.

## Docker Make commands

### Start, build, and test

| Command | Description |
| --- | --- |
| `make docker` | Build and start the application, then start the independent monitoring project. |
| `make docker-app` | Build and start the application without starting monitoring. |
| `make docker SERVICE=gateway` | Build and start the gateway and the frontend (the app opens at `https://localhost:8443`). |
| `make docker SERVICE=<service>` | Build and start the backend service and its declared dependencies. Start the gateway too to call it from the browser. |
| `make frontend-test` | Build and run frontend tests in the development container. |

### Inspect

| Command | Description |
| --- | --- |
| `make ps` | Show the status of application services. |
| `make logs` | Follow logs for all development services. |
| `make logs SERVICE=<service>` | Follow logs for the backend service. |

### Clean up

| Command | Description |
| --- | --- |
| `make down` | Stop the application while leaving monitoring and its volumes running. |
| `make clean` | Stop the development environment and remove project images; database data is preserved. |
| `make reset-db` | Stop the application and remove its Compose-managed volumes, including database data. Monitoring volumes remain. |
| `make fclean` | After confirmation, remove project images and the pgsql and pgvector named volumes. |
| `make re` | Run `clean`, then rebuild and start the development environment. |

## Opening the application

Every container is reached through the gateway (ADR-0006), in development and in production:

- the application: `https://localhost:8443` (`GATEWAY_HTTPS_PORT`);
- `http://localhost:8080` (`GATEWAY_PORT`) only redirects to HTTPS;
- the API, as the frontend calls it: `https://localhost:8443/api/<service>/<resource>`, e.g. `/api/identity/auth/login`.

A service's `/docs`, `/health` and `/internal/...` routes are not reachable through the gateway. To browse a service's `/docs`, run it on the host: `make run SERVICE=<name>`, then open `http://localhost:<service>_PORT/docs`.

### HTTPS certificate

`make secrets` (run by `make docker` and the VM stack targets) creates `shared/secrets/certs/localhost.pem` and `localhost-key.pem` when they are missing: a self-signed certificate for `localhost`. The browser shows a warning for it; accept it once, or trust the certificate instead:

- **With mkcert (recommended):** install [mkcert](https://github.com/FiloSottile/mkcert), then run `mkcert -install` once, and replace the generated files:

  ```bash
  mkcert -cert-file shared/secrets/certs/localhost.pem \
         -key-file shared/secrets/certs/localhost-key.pem \
         localhost 127.0.0.1 ::1
  ```

  `make secrets` keeps existing files, so mkcert's are used from then on. Restart the gateway (`make docker SERVICE=gateway`), and run `make vm-sync` first when the stack runs in the VM.
- **Without mkcert:** import `shared/secrets/certs/localhost.pem` into your browser's or system's trusted certificates.

To get a new self-signed certificate, delete both files and run `make secrets`.

## Independent monitoring

`compose.monitoring.yaml` owns Prometheus, Grafana, and Pushgateway. `make
docker` starts the application and then monitoring; `make down`, `make clean`,
and `make reset-db` affect only the application project. `make monitoring-up`,
`make monitoring-down`, `make monitoring-ps`, and `make monitoring-logs
SERVICE=grafana` manage monitoring independently. The corresponding `-vm`
targets run inside the development VM. Both projects join the external
`DOMAIN-edge` and `DOMAIN-backend` Docker networks, which `make docker` and
`make monitoring-up` create if absent. Grafana continues to query
`http://prometheus:9090` on the backend network.

For an existing installation, stop and remove only the old monitoring
containers once, while preserving their named volumes. Run these commands on
the Docker host (inside `make connect-vm` for a VM):

```bash
docker stop prometheus grafana pushgateway
docker rm prometheus grafana pushgateway
make monitoring-up SECRETS_MODE=validate
```

Before removing them, inspect `docker volume ls` and confirm the existing
`DOMAIN_prometheus_data`, `DOMAIN_grafana_data`, and
`DOMAIN_pushgateway_data` volumes. Replace `DOMAIN` with the `.env` value
(normally `transcendence`). The monitoring Compose file declares those exact
volumes as external, so it reuses their data. Do not run the old application's
`down --volumes` before the move. For a fresh installation, `make
monitoring-up` creates the volumes.

Grafana binds to `127.0.0.1:GRAFANA_PORT` when Docker runs locally. In the VM,
Docker binds Grafana inside the guest and QEMU forwards it to **host loopback**
in every VM network mode. Open `http://127.0.0.1:3000` (or the configured port)
on the host whenever the VM is running. QEMU must be restarted after changing
`GRAFANA_PORT`, because its port forwards are fixed at boot. This access path
is independent of Traefik. The default admin
user is `admin`; read its password from
`shared/secrets/grafana_admin_password`. The provisioned Prometheus data
source and dashboards should appear after Grafana starts.

In Grafana **Explore**, select **Prometheus** and try these queries:

```promql
up
sum by (service) (rate(http_requests_total[5m]))
sum by (service) (rate(http_requests_total{status=~"5.."}[5m]))
ai_worker_last_run_success
probe_success{job="gateway-probe"}
probe_success{job="service-health"}
time() - timestamp(probe_success{job="gateway-probe"})
```

`up` is `1` when Prometheus can scrape a target and `0` when it cannot. The
`gateway-probe` target is different: its `up` means Prometheus reached
Blackbox Exporter, while `probe_success` means Blackbox completed an HTTPS
request through Traefik. The **Services Disponibilty** dashboard shows the
gateway result and age of its last check above the internal service timeline.
Missing probe data appears as **Unknown**, not as healthy.
The **Service /health** timeline shows the five database-backed health checks:
`1` is healthy and `0` is unhealthy. The separate **Metrics scrape
availability** timeline uses `up`; it answers whether Prometheus could collect
`/metrics`, which can still succeed when a service's `/health` check fails.
Both timelines color `0` red and `1` green.

External `/metrics` and `/metrics/...` requests return 404 at Traefik. The
service metrics, Prometheus, Pushgateway, and Blackbox endpoints remain on
internal Docker networks only.

The development probe connects to `https://gateway:8443/` over the shared
edge network and verifies the project's `localhost` certificate using its
mounted public certificate and `server_name: localhost`. The probe also sends
`Host: localhost`, which the development frontend accepts. It never disables TLS
verification. Before deploying a certificate for another hostname, update
`srcs/monitoring/blackbox.yml` to trust that issuer and verify the deployed
hostname; keep the probe target routed through the gateway. A bad certificate
should make `probe_success` become `0`.

The HTTP rates are responses per second; they include API requests handled by the
five FastAPI services, not frontend page or asset requests. A missing 5xx
series can simply mean that service has not returned a 5xx response. The
worker result is absent until a summary run has pushed its gauges to
Pushgateway; `1` means its last run succeeded and `0` means it failed or had
an item generation failure. The **AI Worker** dashboard also shows accepted
article summaries saved and their average processing time in the last run.
`make summarize` runs the worker in the VM's AI Processing container.

To inspect Prometheus **Targets** without publishing Prometheus on the host,
run this on the Docker host. For a VM stack, first enter the VM with
`make connect-vm`, then run the same command there:

```bash
docker exec prometheus wget -qO- 'http://127.0.0.1:9090/api/v1/targets?state=active'
```

The response lists scrape targets and their health. For raw API metrics, query
the service from inside its container. For example:

```bash
docker exec identity python -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8000/metrics").read().decode())'
```

If a target is down or a panel shows no data, check Targets, the raw
`/metrics` output, and the relevant service logs with
`make logs SERVICE=<service>` or `make logs-vm SERVICE=<service>`. For an API
error, the HTTP metric identifies the service and response status; the
exception traceback is in that service's logs. For a failed summary run,
check the `make summarize` output and AI Processing logs. Pushgateway's own
`up=1` shows only that Prometheus can scrape Pushgateway, not that the worker
succeeded.

Prometheus retains data for at most 15 days or 2 GB, whichever limit is hit
first. Allow at least 3 GB for its volume because recent samples and the
write-ahead log can temporarily exceed the retention limit. In shared
environments, keep Grafana bound to localhost or put it behind a deliberate
access policy. Never publish Prometheus, Pushgateway, or service `/metrics`
endpoints through the public gateway, and keep Grafana's admin password out
of version control.

## Development environment

The development override bind-mounts the frontend and backend source code for live reload. Vite's hot reload goes through the gateway too (`wss://localhost:8443`). Apart from the gateway, only the databases, Adminer, and Grafana publish development ports on `127.0.0.1` for use from the host.

### Adminer

Adminer runs with the development database profile. Open `http://localhost:8086` (or `ADMINER_PORT`); it is published on `127.0.0.1` only. Fill the form as follows:

| Field | PostgreSQL | pgvector |
| --- | --- | --- |
| System | PostgreSQL | PostgreSQL |
| Server | `pgsql` | `pgvector` |
| Username | value of `POSTGRES_USER` | value of `POSTGRES_USER` |
| Password | contents of `shared/secrets/postgres_password` | same |
| Database | `postgres`, or `identity_db` after identity bootstrap | same |

Before the identity service starts, the one-shot `prestart-identity` container waits for PostgreSQL, creates the configured identity database if needed, and applies Alembic migrations.

## Production environment

The production environment uses the production Dockerfiles and does not bind-mount application source code.
