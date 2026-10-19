# Local development

Run the frontend and backend processes on your machine. PostgreSQL and pgvector run in a development virtual machine (VM), with their ports available to local backend processes. For VM setup and management, see [README.dev.vm.md](README.dev.vm.md). For containers on the host, see [README.docker.md](README.docker.md).

## Prerequisites and configuration

Install Node.js (see `.node-version`), npm, Python, and `uv` for the processes you run locally. The database command below also needs the host tools and SSH key listed in [VM prerequisites](README.dev.vm.md#prerequisites-and-configuration).

From the repository root, create the shared configuration and each service configuration you need:

```bash
cp .env.example .env
cp srcs/services/identity/.env.example srcs/services/identity/.env
```

Repeat the second command for other backend services. `make init-env` copies **all** `.env.example` files, but overwrites existing `.env` files; use it only when you intend to replace local configuration. The root Makefile reads `.env`, so create it before running Make commands. Keep local `.env` files and generated secrets out of Git. `make vm-databases` creates missing files in `shared/secrets/` on the host through `make secrets`, then synchronizes them into the VM.

## Local Make commands

### Frontend

| Command | Description |
| --- | --- |
| `make frontend-install` | Install frontend dependencies. |
| `make frontend` | Start Vite on `FRONTEND_PORT` (default `5173`). |
| `make frontend-build` | Check the production build. |

For direct npm, test, and lint commands, see [srcs/frontend/DEV_DOC.md](srcs/frontend/DEV_DOC.md).

### Backend

| Command | Description |
| --- | --- |
| `make list-services` | List available backend service names. |
| `make sync SERVICE=identity` | Install the selected service's Python dependencies. |
| `make run SERVICE=identity` | Start the service locally after starting VM databases and ensuring its database exists. |
| `make test SERVICE=identity` | Run service tests locally with VM databases available. |
| `make lint SERVICE=identity` | Lint the service locally. |
| `make typecheck SERVICE=identity` | Type-check the service locally. |
| `make status SERVICE=identity` | Show the service's migration status. |
| `make migration SERVICE=identity MESSAGE="add users table"` | Generate an Alembic database migration. Review it before applying it. |
| `make upgrade SERVICE=identity` | Apply database migrations. |
| `make downgrade SERVICE=identity` | Revert the latest migration by default. |

Run `make sync SERVICE=identity` after cloning or when that service's dependencies change. `run`, `test`, and the migration commands start or reuse the VM in `local-backend` network mode and start PostgreSQL and pgvector there. `run` and migration commands also ensure the service database exists. Each backend owns its own database and migrations; do not edit another service's database directly.

## Databases in the VM

Start just the databases when you want them available without starting a backend:

```bash
make vm-databases
```

The command starts or reuses the VM in `local-backend` network mode, starts the database containers, and makes PostgreSQL available at `localhost:5432` (`POSTGRES_PORT`) and pgvector at `localhost:5433` (`AI_POSTGRES_PORT`). Local backends use `POSTGRES_HOST=localhost` from `.env`. If the VM is running in another network mode, the command restarts it so those database ports are forwarded. For database logs or VM shutdown, see [VM Make commands](README.dev.vm.md#vm-make-commands).

## Next step

Run `make vm-databases`, then `make run SERVICE=identity` in one terminal and `make frontend` in another. Verify that the frontend opens at `http://localhost:5173` and the identity service can connect to its database.
