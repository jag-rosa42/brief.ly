# Container environments

This guide covers the Podman Compose development and production environments. For running services directly on your machine, see [README.dev.md](README.dev.md).

## Prerequisites and configuration

Install Podman with the `podman compose` plugin, then create the shared environment file and service configuration files:

```bash
cp .env.example .env
cp srcs/services/identity/.env.example srcs/services/identity/.env
```

Container targets create `shared/secrets/postgres_password` automatically when it does not exist; do not commit this file. PostgreSQL and pgvector store their data in Podman-managed named volumes

The production environment loads `compose.yaml`. Development commands also load `compose.override.yaml`; macOS additionally loads `compose.mac.yaml` to enable filesystem polling for the frontend bind mount.

## Docker Make commands

### Start, build, and test

| Command | Description |
| --- | --- |
| `make dev-docker` | Build and start all enabled development services in the background. |
| `make dev-docker SERVICE=frontend` | Build and start the frontend service and its declared dependencies. |
| `make dev-docker SERVICE=<service>` | Build and start the backend service and its declared dependencies. |
| `make frontend-test` | Build and run frontend tests in the development container. |
| `make prod` | Build all production images without cache, then start all enabled production services in the foreground. |

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

## Development environment

The development override bind-mounts frontend and identity source code for live reload. Frontend HMR is configured for the host browser, and each service's API is exposed on `<service>_PORT`.

### Adminer

Adminer runs with the development database profile. Open `http://localhost:8086` (or `ADMINER_PORT`). Fill the form as follows:

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
