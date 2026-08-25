# Frontend development

Run local frontend commands from the repository root:

```bash
make frontend-install  # install dependencies
make frontend          # start the Vite development server
make frontend-build    # create a production build
```

The development server listens on `FRONTEND_PORT` from the root `.env` file (default `5173`).

These Make targets are convenience wrappers for the frontend package commands. You can also work directly in `srcs/frontend` when you only need frontend tooling:

```bash
cd srcs/frontend
npm install       # install dependencies declared in package.json
npm run dev       # start Vite with live reload
npx vitest --watch  # run tests continuously while coding
npm run lint      # lint the React and TypeScript source
npm run build     # verify the production build
```

Run `npm install` after cloning the project, after frontend dependencies change, or if `node_modules` has been removed. Use `npm run dev` for a frontend-only local session; use `make dev-docker` when you need the containerised frontend together with backend services and databases.

## Containerised frontend

Use the root Make targets rather than invoking Compose against a frontend-specific compose file:

```bash
make dev-docker SERVICE=frontend  # build and run the frontend development container
make frontend-test                # run Vitest in a development container
make logs SERVICE=frontend        # view its logs
make down                         # stop the development stack
```

The development Compose override bind-mounts `srcs/frontend` into `/app` and keeps `node_modules` in a named volume. It configures Vite HMR for the host browser. On macOS, `compose.mac.yaml` enables polling to ensure file changes are detected through the bind mount.

For the full frontend, backend, and database development environment, run:

```bash
make dev-docker
```
