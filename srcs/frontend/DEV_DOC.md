# Frontend commands

Run these commands from the `frontend` directory.

```bash
# Install dependencies
npm install

# Start the React development server with live reload
npm run dev

# Run tests continuously while coding
npx vitest --watch

# Lint the React and TypeScript code
npm run lint

# Check the production build
npm run build
```

## Podman Compose

```bash
# Build all images
podman compose build

# Rebuild all images without using the cache
podman compose build --no-cache

# Start the development container
podman compose up front-dev

# Start the development container in the background
podman compose up -d front-dev

# Start the production container in the background
podman compose up -d front-prod

# Rebuild and restart one service
podman compose up -d --build front-dev

# List project containers
podman compose ps

# Follow all logs
podman compose logs -f

# Follow one service's logs
podman compose logs -f front-dev

# Open a shell in the running development container
podman compose exec front-dev sh

# Run a one-off shell in a new development container
podman compose run --rm front-dev sh

# Restart one service
podman compose restart front-dev

# Stop the project containers
podman compose stop

# Stop and remove the project containers and network
podman compose down

# Stop and remove containers, network, and project volumes
podman compose down --volumes

# Start the optional test service
podman compose --profile front-test up front-test
```

## Podman

```bash
# List running containers
podman ps

# List all containers
podman ps -a

# List local images
podman images

# List volumes
podman volume ls

# Follow a container's logs
podman logs -f <container-name-or-id>

# Inspect a container
podman inspect <container-name-or-id>

# Show live container resource usage
podman stats

# Open a shell in a running container
podman exec -it <container-name-or-id> sh

# Stop a container
podman stop <container-name-or-id>

# Start a stopped container
podman start <container-name-or-id>

# Restart a container
podman restart <container-name-or-id>

# Remove a stopped container
podman rm <container-name-or-id>

# Remove an image
podman rmi <image-name-or-id>

# Remove unused containers, images, networks, and build cache
podman system prune
```
