# Container environments

This guide covers the Podman Compose development and production environments. For running services directly on your machine, see [README.dev.md](README.dev.md).

## Prerequisites and configuration

Install Podman with the `podman compose` plugin, then create the shared environment file and service configuration files:

```bash
cp .env.example .env
cp srcs/services/identity/.env.example srcs/services/identity/.env
```

Set `DATABASES_VOLUME_DIR` in `.env` to a persistent data location. Container targets create `shared/secrets/postgres_password` automatically when it does not exist; do not commit this file.

The production environment loads `compose.yaml`. Development commands also load `compose.override.yaml`; macOS additionally loads `compose.mac.yaml` to enable filesystem polling for the frontend bind mount.

## Development environment

Start all enabled development profiles in the foreground:

```bash
make dev-docker
```

Start a single service and its declared dependencies:

```bash
make dev-docker SERVICE=frontend
make dev-docker SERVICE=identity
```

The development override bind-mounts frontend and identity source code for live reload. Frontend HMR is configured for the host browser, and the identity API is exposed on `IDENTITY_PORT` (default `8081`).

Run frontend tests in the development container:

```bash
make frontend-test
```

### Adminer

Adminer runs with the development database profile. Open `http://localhost:8086` (or `ADMINER_PORT`). Fill the form as follows:

| Field | PostgreSQL | pgvector |
| --- | --- | --- |
| System | PostgreSQL | PostgreSQL |
| Server | `pgsql` | `pgvector` |
| Username | value of `POSTGRES_USER` | value of `POSTGRES_USER` |
| Password | contents of `shared/secrets/postgres_password` | same |
| Database | `postgres`, or `identity_db` after identity bootstrap | `postgres` |

Before the identity service starts, the one-shot `prestart-identity` container waits for PostgreSQL, creates the configured identity database if needed, and applies Alembic migrations.

## Production environment

Build without cache and run all production profiles:

```bash
make prod
```

The production environment uses the production Dockerfiles and does not bind-mount application source code.

## Container operations

```bash
make ps
make logs
make logs SERVICE=identity
make down
make clean
make re
```

`make down` stops the development Compose environment. `make clean` stops it and removes Compose volumes and images; `make re` runs `clean` followed by `dev-docker`. Database storage is bind-mounted under `DATABASES_VOLUME_DIR`, so remove those host directories separately only when you intentionally want to delete the data.
