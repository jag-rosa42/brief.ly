# VM development environment

Run the development Compose stack inside an Ubuntu virtual machine (VM). QEMU runs the guest, and Docker Compose runs the services inside it. This gives the stack a separate Linux runtime while forwarding browser-facing ports to your host. For locally running application processes with VM databases, see [README.dev.md](README.dev.md). For Compose on the host, see [README.docker.md](README.docker.md).

## Prerequisites and configuration

Install QEMU, `rsync`, Python 3, an SSH client, and `make` on the host. Configure QEMU hardware acceleration and firmware for your host. The first VM boot downloads a pinned Ubuntu 24.04 cloud image and installs Docker and Compose in the guest, so network access is needed. These prerequisites also apply when [local development](README.dev.md) uses `make vm-databases`.

Create the shared configuration, each service configuration, and ensure the SSH public key specified by `SSH_PUBLIC_KEY` exists (default `~/.ssh/id_rsa.pub`):

```bash
cp .env.example .env
cp srcs/services/identity/.env.example srcs/services/identity/.env
```

Repeat the service copy for each backend you plan to run. The root Makefile reads `.env`; `make init-env` overwrites existing `.env` files, so use it only to reset local configuration. `make vm`, `make vm-databases`, and `make prod` generate missing secrets on the host before synchronizing the project, including `.env` and `shared/secrets/`, into the guest. The guest uses those synced secrets, and `make secrets` is rejected there. Keep these files out of Git and edit the host copy: a later sync can replace guest-side edits.

If you do not have a key pair at the default path, run `ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa` to create `~/.ssh/id_rsa` and `~/.ssh/id_rsa.pub`. Do not overwrite an existing private key. The public key is used to create the guest account; keep the private key on your host.

## Default Ubuntu and Docker versions

New guests use the defaults defined in [the VM configuration script](shared/script/create-vm/config.sh). Pinning the image build and package versions gives developers the same starting environment.

| Component | Default version | Override variable |
| --- | --- | --- |
| Ubuntu cloud image | 24.04 LTS (Noble), image build `20260926`; `amd64` or `arm64` to match the host | Fixed in the script |
| Docker Engine and CLI (`docker-ce`, `docker-ce-cli`) | `5:29.9.0-1~ubuntu.24.04~noble` | `DOCKER_ENGINE_VERSION` |
| Docker Compose plugin (`docker-compose-plugin`) | `5.6.0-1~ubuntu.24.04~noble` | `DOCKER_COMPOSE_VERSION` |
| Docker Buildx plugin (`docker-buildx-plugin`) | `0.38.0-1~ubuntu.24.04~noble` | `DOCKER_BUILDX_VERSION` |
| Container runtime (`containerd.io`) | `2.4.1-2~ubuntu.24.04~noble` | `CONTAINERD_VERSION` |

The Docker entries are exact Ubuntu package version strings, including their packaging prefixes and suffixes. Compose manages the service stack, Buildx builds container images, and containerd runs containers underneath Docker. The first-boot setup installs these packages from Docker's Ubuntu package repository.

To override a Docker package version, export its variable on the host before creating a new guest, using a complete package version available for Ubuntu 24.04 and the guest architecture. These settings apply during first-boot installation; changing them does not upgrade an existing guest.

To inspect the installed versions, run `make connect-vm` on the host, then run these commands inside the guest:

```bash
cat /etc/os-release
dpkg-query -W docker-ce docker-ce-cli docker-compose-plugin docker-buildx-plugin containerd.io
docker version
docker compose version
docker buildx version
```

`dpkg-query` reports the exact installed package versions for comparison with the table; the Docker commands report the versions of the available tools and running Engine.

## VM lifecycle

Run these commands from the repository root after creating `.env` and checking your SSH public key. The VM's virtual disk and Docker volumes live in `vm/`; they persist when you stop the guest.

### `make launch-vm`: start or reuse the guest

Use this when you need a running guest or want to copy recent host changes into it. If the VM is stopped, the command starts QEMU; on first use, it creates the disk and first-boot configuration, downloads Ubuntu, and waits for guest setup to finish. It then synchronizes the host project, including local configuration and secrets, into the guest. If the VM is already reachable over SSH, it keeps the current guest and network mode and only waits for setup and synchronizes files. It does **not** start the application containers; use `make vm` or `make vm SERVICE=identity` for those.

The default network mode forwards development service ports. QEMU fixes port forwarding at boot, so stop the VM before using `make launch-vm VM_NETWORK_MODE=local-backend` or another mode. `make vm-databases` handles that restart automatically for local backend development.

### `make connect-vm`: open a guest shell

Use this to inspect the guest directly. It runs `make launch-vm` first, so it may start the VM and always synchronizes the host project before opening an interactive SSH shell. Run `exit` to return to your host terminal; the VM stays running. Edit source, `.env`, and secrets on the host: a later sync can overwrite guest-side changes, and changes made in the guest are not copied back.

### `make stop-vm`: shut down without deleting data

Use this when you are finished or need to change the network mode. The command requests a clean guest shutdown and waits for QEMU to exit. It preserves the VM disk, Docker volumes, database data, and synced files. If the VM is already stopped, there is nothing to shut down. The next `make launch-vm` starts the same guest. To stop only Compose containers while leaving the guest running, use `make down-vm`.

### `make create-vm`: replace the guest and its data

Use this only when you need a completely fresh VM. The command asks for confirmation, stops the guest, removes the repository's `vm/` directory, and launches and synchronizes a new VM. This deletes the guest operating system changes, Docker images, named volumes, and **all database data stored on that disk**. There is no automatic rollback; back up data you need before confirming. To clear only Compose-managed volumes, use `make reset-db-vm` instead.

## VM Make commands

### Start and use

| Command | Description |
| --- | --- |
| `make vm` | Restart in development network mode, synchronize the project, then build and start the complete Compose stack in the guest. |
| `make vm SERVICE=identity` | Restart in development mode and start one Compose service plus its dependencies. |
| `make vm SERVICE=adminer` | Start Adminer and its database dependencies in the guest. |
| `make frontend-test-vm` | Run frontend tests in the guest's development container. |

The VM starts with Docker installed by cloud-init (Ubuntu's first-boot setup). The Makefile waits for that setup and then copies the host project with `rsync`. `make vm` restarts the guest each time because QEMU's port forwards are fixed when it starts. In development mode, host `localhost` receives the configured frontend, backend, Adminer, and database ports; for example, `http://localhost:5173` opens the frontend and `http://localhost:8086` opens Adminer with the default `.env`.

### Inspect

| Command | Description |
| --- | --- |
| `make ps-vm` | Show Compose container status in the guest. |
| `make logs-vm` | Follow logs for all development services in the guest. |
| `make logs-vm SERVICE=identity` | Follow one service's logs in the guest. |
| `make connect-vm` | Start or reuse the guest, sync the project, and open an interactive SSH session. |

### Clean up

| Command | Description |
| --- | --- |
| `make down-vm` | Stop guest containers while preserving named volumes. |
| `make stop-vm` | Shut down the guest while preserving its virtual disk and database data. |
| `make clean-vm` | Stop guest containers and remove project images; preserve database volumes. |
| `make re-vm` | Clean, then rebuild and start the development stack in the guest. |
| `make reset-db-vm` | Remove Compose-managed volumes, including database data. |
| `make fclean-vm` | After confirmation, remove project images and database volumes. |
| `make create-vm` | After confirmation, replace the guest disk and all data stored in `vm/`. |

The Docker volumes live on the VM disk. `down-vm` and `stop-vm` retain data; `reset-db-vm`, `fclean-vm`, and `create-vm` discard data at different scopes. Back up anything important before using those reset commands. `create-vm` also replaces guest operating-system changes.

## Development and production networking

Development mode forwards the configured frontend, API, Adminer, and database ports from guest to host `127.0.0.1`. For local backend work, `make vm-databases` uses a separate `local-backend` mode that forwards only database ports, leaving app ports free for processes on the host. `make prod` restarts in production mode and forwards only `GATEWAY_PORT` (default `8080`), then builds and runs production Compose in the guest foreground. Switching modes requires a VM restart; use the corresponding Make target instead of assuming an already running guest has the required forwards.

The VM copies source and configuration from the host, so make source changes on the host and run `make launch-vm` to synchronize them. The development Compose override bind-mounts frontend and identity source code for live reload. Other services may need a rebuild through `make vm SERVICE=<name>` to pick up code changes.

## Next step

Run `make vm SERVICE=identity`, then `make ps-vm`. Confirm that the identity service and its dependencies are running, and open `http://localhost:8081/docs` with the default `IDENTITY_PORT`.
