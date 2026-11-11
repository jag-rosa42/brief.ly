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
| `make docker` | Build and start all enabled development services in the background. |
| `make docker SERVICE=gateway` | Build and start the gateway and the frontend (the app opens at `https://localhost:8443`). |
| `make docker SERVICE=<service>` | Build and start the backend service and its declared dependencies. Start the gateway too to call it from the browser. |
| `make frontend-test` | Build and run frontend tests in the development container. |

### Inspect

| Command | Description |
| --- | --- |
| `make ps` | Show the status of development services. |
| `make logs` | Follow logs for all development services. |
| `make logs SERVICE=<service>` | Follow logs for the backend service. |

### Clean up

| Command | Description |
| --- | --- |
| `make down` | Stop the development environment while preserving named volumes. |
| `make clean` | Stop the development environment and remove project images; database data is preserved. |
| `make reset-db` | Stop the development environment and remove Compose-managed volumes, including database data. |
| `make fclean` | After confirmation, remove project images and the pgsql and pgvector named volumes. |
| `make re` | Run `clean`, then rebuild and start the development environment. |

## Opening the application

Every container is reached through the gateway (ADR-0006), in development and in production:

- the application: `https://localhost:8443` (`GATEWAY_HTTPS_PORT`);
- `http://localhost:8080` (`GATEWAY_PORT`) only redirects to HTTPS;
- the API, as the frontend calls it: `https://localhost:8443/api/<service>/<resource>`, e.g. `/api/identity/auth/login`.

A service's `/docs`, `/health` and `/internal/...` routes are not reachable through the gateway. To browse a service's `/docs`, run it on the host: `make run SERVICE=<name>`, then open `http://localhost:<service>_PORT/docs`.

### HTTPS certificate

`make secrets` (run by `make docker` and `make vm`) creates `shared/secrets/certs/localhost.pem` and `localhost-key.pem` when they are missing: a self-signed certificate for `localhost`. The browser shows a warning for it; accept it once, or trust the certificate instead:

- **With mkcert (recommended):** install [mkcert](https://github.com/FiloSottile/mkcert), then run `mkcert -install` once, and replace the generated files:

  ```bash
  mkcert -cert-file shared/secrets/certs/localhost.pem \
         -key-file shared/secrets/certs/localhost-key.pem \
         localhost 127.0.0.1 ::1
  ```

  `make secrets` keeps existing files, so mkcert's are used from then on. Restart the gateway (`make docker SERVICE=gateway`), and run `make vm-sync` first when the stack runs in the VM.
- **Without mkcert:** import `shared/secrets/certs/localhost.pem` into your browser's or system's trusted certificates.

To get a new self-signed certificate, delete both files and run `make secrets`.

## Observability in development

`make docker` starts the `observability` Compose profile with Prometheus,
Grafana, and Pushgateway. Use `make ps` to check the containers,
`make logs SERVICE=grafana` (or `prometheus` or `pushgateway`) to inspect logs,
and `make down` to stop the stack without removing its named volumes. For the
development VM, use `make vm`, `make ps-vm`, `make logs-vm SERVICE=grafana`,
and `make down-vm` instead.

Open Grafana at `http://127.0.0.1:3000`, or at the `GRAFANA_PORT` configured in
`.env`. The same host address works for a development VM because that port is
forwarded. The default admin user is `admin`; read its password from
`shared/secrets/grafana_admin_password`. The provisioned Prometheus data
source and dashboards should appear after Grafana starts.

In Grafana **Explore**, select **Prometheus** and try these queries:

```promql
up
sum by (service) (rate(http_requests_total[5m]))
sum by (service) (rate(http_requests_total{status=~"5.."}[5m]))
ai_worker_last_run_success
```

`up` is `1` when Prometheus can scrape a target and `0` when it cannot. The
HTTP rates are responses per second; they include API requests handled by the
five FastAPI services, not frontend page or asset requests. A missing 5xx
series can simply mean that service has not returned a 5xx response. The
worker result is absent until a summary run has pushed its gauges to
Pushgateway; `1` means its last run succeeded and `0` means it failed or had
an item generation failure. `make summarize` runs the worker in the VM's AI
Processing container.

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
