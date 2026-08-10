## Getting Started

### Frontend

The frontend dependencies must be installed before starting the development server.

From the project root:

```bash
# Install frontend dependencies
make frontend-install

# Start the frontend development server
make frontend
```

The first command installs the dependencies defined in `srcs/frontend/package.json` (including Vite). You only need to run it again when the frontend dependencies change or `node_modules` is removed.

### Backend services

Before running a backend service, create its `.env` file from the provided `.env.example`:

```bash
cp srcs/services/identity/.env.example srcs/services/identity/.env
```
Then update the `.env` file with the appropriate values for your local environment.

Backend services can be run individually by specifying the service name:

```bash
make run SERVICE=identity
```

Other available service commands include:

```bash
make migration SERVICE=identity
make upgrade SERVICE=identity
make downgrade SERVICE=identity
make test SERVICE=identity
make lint SERVICE=identity
make typecheck SERVICE=identity
make shell SERVICE=identity
```

To see the available services:

```bash
make list-services
```

### Docker

To start the complete stack with Docker Compose:

```bash
make build
make up
```

Useful Docker commands:

```bash
make ps       # Show running containers
make logs     # Follow logs for all services
make logs SERVICE=identity  # Follow logs for one service
make down     # Stop the stack
```

### Quick start

For local frontend + backend development:

```bash
# Install frontend dependencies (first time only)
make frontend-install

# Start the frontend
make frontend

# In another terminal, start a backend service
make run SERVICE=identity
```
