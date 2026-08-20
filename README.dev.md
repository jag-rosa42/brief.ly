# Local development guide

This guide is for running the frontend and backend services directly on your machine. For containerised development and production environments, see [README.docker.md](README.docker.md).

## Initial setup

Create the shared environment file and the configuration file for every service you plan to run:

```bash
cp .env.example .env
cp srcs/services/identity/.env.example srcs/services/identity/.env
```

Set `DATABASES_VOLUME_DIR` in `.env` to the location where local database data should persist. For a locally run backend service, provide the shared database connection values and `POSTGRES_PASSWORD` in its environment or service `.env` file.

## Frontend

From the repository root:

```bash
make frontend-install  # install dependencies
make frontend          # start Vite
make frontend-build    # build for production
```

The frontend listens on `FRONTEND_PORT` (default `5173`). For direct npm, testing, and linting commands, see [srcs/frontend/DEV_DOC.md](srcs/frontend/DEV_DOC.md).

## Local backend services

Start a backend service from the repository root:

```bash
make run SERVICE=identity
```

Available service commands include:

```bash
make migration SERVICE=identity
make upgrade SERVICE=identity
make downgrade SERVICE=identity
make test SERVICE=identity
make lint SERVICE=identity
make typecheck SERVICE=identity
make shell SERVICE=identity
make list-services
```

## Database containers for local services

Backend services run locally, while PostgreSQL and pgvector run in containers. Start both database containers in the background with:

```bash
make dev-databases
```

This command creates the database data directories below `DATABASES_VOLUME_DIR`, generates `shared/secrets/postgres_password` when it is missing, and starts `pgsql` and `pgvector`.

The databases are available from the host at:

- `pgsql`: `POSTGRES_PORT` (default `5432`)
- `pgvector`: `AI_POSTGRES_PORT` (default `5433`)

### Adminer

Adminer runs as a container, so start it with:

```bash
make dev-docker SERVICE=adminer
```

Open `http://localhost:8086` (or `ADMINER_PORT`). Fill the form as follows:

| Field | PostgreSQL | pgvector |
| --- | --- | --- |
| System | PostgreSQL | PostgreSQL |
| Server | `pgsql` | `pgvector` |
| Username | value of `POSTGRES_USER` | value of `POSTGRES_USER` |
| Password | contents of `shared/secrets/postgres_password` | same |
| Database | `postgres`, or `identity_db` after identity bootstrap | `postgres` |

Inspect the database containers and their logs with:

```bash
make ps
make logs SERVICE=pgsql
make logs SERVICE=pgvector
```

Stop the Compose environment when you are finished:

```bash
make down
```

`make clean` also removes Compose volumes and images. The database files are bind-mounted below `DATABASES_VOLUME_DIR`; keep or remove that directory deliberately according to whether you need to retain local data.
