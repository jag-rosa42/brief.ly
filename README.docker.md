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

## Development environment

The development override bind-mounts the frontend and backend source code for live reload. Vite's hot reload goes through the gateway too (`wss://localhost:8443`). No service publishes a port: only the databases and Adminer do, on `127.0.0.1`, for the commands that run on the host.

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
