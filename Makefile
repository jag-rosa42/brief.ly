# Pure dispatcher — no build logic lives here. Forwards whatever
# target was invoked down to the chosen service's own Makefile.

include .env
include shared/mk/colors.mk
include shared/mk/secrets.mk
include shared/mk/ingest.mk
include shared/mk/llm.mk
include shared/mk/backup_recovery.mk
include shared/mk/monitoring.mk


NAME := Transcendence
.DEFAULT_GOAL := help

# ============================================================================ #
#                                     OS                                       #
# ============================================================================ #
OS := $(shell uname -s)

# ============================================================================ #
#                                DIRECTORIES                                   #
# ============================================================================ #

SRC_DIR := srcs
FRONTEND_DIR := srcs/frontend
SERVICES_DIR := srcs/services

# ============================================================================ #
#                               VARIABLES & FLAGS                              #
# ============================================================================ #

MAKE_CMD ?= $(MAKE)
COMPOSE := docker compose
CONTAINER_CMD := docker
ENV_FILE := .env
ENV_EXAMPLE_FILES := .env.example $(wildcard $(SERVICES_DIR)/*/.env.example)


# ============================================================================ #
#                                  DOCKER VARS                                 #
# ============================================================================ #

PROD_COMPOSE_FILE := compose.yaml
DEV_COMPOSE_FILE := compose.yaml compose.override.yaml
DEV_COMPOSE = $(COMPOSE) $(addprefix -f ,$(DEV_COMPOSE_FILE))
PROD_COMPOSE = $(COMPOSE) $(addprefix -f ,$(PROD_COMPOSE_FILE))
COMPOSE_PROFILES := frontend backend databases
COMPOSE_PROFILES_ALL := $(addprefix --profile ,$(COMPOSE_PROFILES))
COMPOSE_CLEAN_PROFILES_ALL := $(COMPOSE_PROFILES_ALL) --profile front-test

#for mac OS
ifeq ($(OS),Darwin)
DEV_COMPOSE_FILE += compose.mac.yaml
endif

# ============================================================================ #
#                                  VM VARS                                     #
# ============================================================================ #

#override from .env file
VM_DIR ?= $(CURDIR)/vm
SSH_PUBLIC_KEY ?= $(HOME)/.ssh/id_rsa.pub
VM_SSH_PORT ?= 2222
GRAFANA_PORT ?= 3000

VM_NETWORK_MODE ?= dev
VM_SCRIPT=./shared/script/create-vm.sh
VM_USERNAME=$(shell id -un)
VM_REMOTE_DIR ?= /home/$(VM_USERNAME)/ft_transcendance
VM_SSH_OPTIONS := -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
	-o ConnectTimeout=5 -p $(VM_SSH_PORT)
VM_SSH := ssh $(VM_SSH_OPTIONS) $(VM_USERNAME)@127.0.0.1
VM_SSH_TTY := ssh -tt $(VM_SSH_OPTIONS) $(VM_USERNAME)@127.0.0.1
VM_RSYNC_SSH := ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -p $(VM_SSH_PORT)
VM_QEMU_ENV := VM_DIR="$(VM_DIR)" VM_USERNAME="$(VM_USERNAME)" \
	SSH_PUBLIC_KEY="$(SSH_PUBLIC_KEY)" \
	SSH_PORT="$(VM_SSH_PORT)" VM_NETWORK_MODE="$(VM_NETWORK_MODE)" \
	GATEWAY_PORT="$(GATEWAY_PORT)" GATEWAY_HTTPS_PORT="$(GATEWAY_HTTPS_PORT)" \
	ADMINER_PORT="$(ADMINER_PORT)" GRAFANA_PORT="$(GRAFANA_PORT)" \
	POSTGRES_PORT="$(POSTGRES_PORT)" AI_POSTGRES_PORT="$(AI_POSTGRES_PORT)"
# Inside the VM, Compose publishes databases, Adminer, and Grafana on every
# guest address: QEMU forwards to the guest's network address, not its loopback.
# QEMU itself only listens on the host's 127.0.0.1.
VM_REMOTE_ENV := VM_GUEST_BIND_ADDRESS=0.0.0.0
VM_DOCKER_TARGETS := logs ps down re clean reset-db frontend-test $(MONITORING_TARGETS)


# ============================================================================ #
#                                  🫡HELP                                      #
# ============================================================================ #

help:
	@printf "\n$(BLUE_COLOR)🚀 $(NAME) — available commands$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 💻 Dev local ─────────────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(GREEN_COLOR)  Frontend$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) frontend                    $(CYAN_COLOR)Start the frontend locally$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) frontend-install            $(CYAN_COLOR)Install frontend dependencies$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) frontend-build              $(CYAN_COLOR)Build the frontend$(DEFAULT_COLOR)\n"
	@printf "$(GREEN_COLOR)  Databases$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) vm-databases                $(CYAN_COLOR)Start PostgreSQL and pgvector in the VM for local backend development$(DEFAULT_COLOR)\n"
	@printf "$(GREEN_COLOR)  Backend$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) test SERVICE=<name>         $(CYAN_COLOR)Run service tests locally with a VM test database$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) lint SERVICE=<name>         $(CYAN_COLOR)Lint a service locally$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) run SERVICE=<name>          $(CYAN_COLOR)Run one backend locally with databases in the VM$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) sync SERVICE=<name>         $(CYAN_COLOR)Synchronize service dependencies$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) typecheck SERVICE=<name>    $(CYAN_COLOR)Type-check a service locally$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) status SERVICE=<name>       $(CYAN_COLOR)Show migration status against the VM database$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) clear-cache SERVICE=<name>  $(CYAN_COLOR)Clear service cache$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) migration SERVICE=<name>    $(CYAN_COLOR)Create a migration using the VM database$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) upgrade SERVICE=<name>      $(CYAN_COLOR)Apply migrations to the VM database$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) downgrade SERVICE=<name>    $(CYAN_COLOR)Revert migrations in the VM database$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) list-services               $(CYAN_COLOR)List available backend services$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) reinstall SERVICE=<name>    $(CYAN_COLOR)Reinstall dependencies for a service$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 🐳 Dev Docker ─────────────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) docker                      $(CYAN_COLOR)Start the application and monitoring in host Docker$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) docker-app                  $(CYAN_COLOR)Start only the application stack in host Docker$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) docker SERVICE=<name>       $(CYAN_COLOR)Run one Compose service and its dependencies in host Docker$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) frontend-test               $(CYAN_COLOR)Run frontend tests in Docker$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 🦙 Ollama ─────────────────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) ollama                     $(CYAN_COLOR)Start local Ollama and pull the small summary model$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) ollama-down                $(CYAN_COLOR)Stop the Ollama server started by make$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── ⚙️  Worker ────────────────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) ingest                      $(CYAN_COLOR)Trigger ingestion through a locally running content-management service$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) clear-summaries-vm          $(CYAN_COLOR)Reset VM summaries and rejection decisions; preserve articles$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) ingest-vm                   $(CYAN_COLOR)Trigger ingestion through content-management in the VM$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) clear-articles-vm           $(CYAN_COLOR)Confirm deletion of VM articles, summaries, and saved snapshots; preserve users$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) ingest-docker               $(CYAN_COLOR)Trigger ingestion through content-management in the docker$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) summarize                   $(CYAN_COLOR)Run the summary worker in the VM's AI Processing container$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) stop-summarize              $(CYAN_COLOR)Stop summary workers inside the VM; keep the API running$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 🔧 Stack preparation ─────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) init-env                    $(CYAN_COLOR)Force generating .env files from their .env.example templates$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) secrets                     $(CYAN_COLOR)Create missing secrets$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 🚀 Production ─────────────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) prod                        $(CYAN_COLOR)Build and run the production stack inside the VM$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 📦 Shared container tools ────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(CYAN_COLOR)  Add -vm to logs, ps, down, reset-db, clean, re, or fclean to run them in the VM.$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) logs [SERVICE=<name>]       $(CYAN_COLOR)Follow container logs$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) ps                          $(CYAN_COLOR)Show container status$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) down                        $(CYAN_COLOR)Stop containers$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) reset-db                    $(CYAN_COLOR)Reset database data 🚨$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) clean                       $(CYAN_COLOR)Stop containers and remove project images$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) re                          $(CYAN_COLOR)Clean and rebuild the stack$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) fclean                      $(CYAN_COLOR)Reset database data and remove project images 🚨$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 🖥️  VM development ───────────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) vm-full-stack               $(CYAN_COLOR)Start the application and monitoring inside the VM$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) vm-app                      $(CYAN_COLOR)Start only the application stack inside the VM$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) vm-service SERVICE=<name>    $(CYAN_COLOR)Start one Compose service and its dependencies inside the VM$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) create-vm                   $(CYAN_COLOR)Confirm and recreate vm/, then leave the new VM running$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) launch-vm                   $(CYAN_COLOR)Start the development VM, wait for SSH, and sync this project$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) vm-sync                     $(CYAN_COLOR)Synchronize project files to the running VM$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) connect-vm                  $(CYAN_COLOR)Open an interactive SSH session in the VM$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) stop-vm                     $(CYAN_COLOR)Shut down the guest cleanly$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) debug-create-vm             $(CYAN_COLOR)Start QEMU interactively for boot troubleshooting$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 📦 Backups ────────────────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) backup                      $(CYAN_COLOR)Create and verify an encrypted host backup$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) backup-schedule-install [BACKUP_TIME=HHMM]  $(CYAN_COLOR)Install daily host cron for make backup (default 0200)$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) backup-list                 $(CYAN_COLOR)List completed host backup sets$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) backup-retention-preview    $(CYAN_COLOR)Preview which backup sets retention would keep$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) backup-prune [APPLY=1]      $(CYAN_COLOR)Report backup storage and optionally remove old sets$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) backup-extract BACKUP_SET=id  $(CYAN_COLOR)Decrypt into a new host directory$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) backup-restore BACKUP_SET=id  $(CYAN_COLOR)Recreate the configured VM, restore its backup, and start the stack$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) backup-verify BACKUP_SET=id  $(CYAN_COLOR)Verify one encrypted backup set$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 📈 Monitoring ─────────────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) monitoring-up               $(CYAN_COLOR)Start the independent monitoring project$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) monitoring-down             $(CYAN_COLOR)Stop monitoring, preserving its volumes$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) monitoring-ps               $(CYAN_COLOR)Inspect monitoring containers$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) monitoring-logs [SERVICE=name] $(CYAN_COLOR)Follow monitoring logs$(DEFAULT_COLOR)\n"
	@printf "$(CYAN_COLOR)  Add -vm to these targets to run them in the VM; Grafana is on host 127.0.0.1:$(GRAFANA_PORT).$(DEFAULT_COLOR)\n\n"


# ============================================================================ #
#                                  LOCAL DEV                                  #
# ============================================================================ #

# ---- Frontend dispatch ----
frontend:
	@$(call print,$(GREEN_COLOR),[FRONTEND] Starting frontend...)
	@$(MAKE) -C $(FRONTEND_DIR) dev -s

frontend-install:
	@$(call print,$(BLUE_COLOR),[FRONTEND] Installing dependencies...)
	@$(MAKE) -C $(FRONTEND_DIR) install -s

frontend-build:
	@$(call print,$(BLUE_COLOR),[FRONTEND] Building frontend...)
	@$(MAKE) -C $(FRONTEND_DIR) build -s

frontend-test:
	@$(call print,$(BLUE_COLOR),[FRONTEND] Running tests in Docker...)
	@$(DEV_COMPOSE) --profile front-test up --build front-test

list-frontend:
	@$(call print,$(BLUE_COLOR),Frontend commands:)
	@printf "  make frontend          Start development server\n"
	@printf "  make frontend-install  Install dependencies\n"
	@printf "  make frontend-build    Build for production\n"

# ---- Backend development & service orchestration ----

#.env from .env.example
init-env:
	@$(call print,$(GREEN_COLOR),[ENV] Forcing generation of .env files from templates...)
	@for path_to_env_example in $(ENV_EXAMPLE_FILES); do \
		env_file="$${path_to_env_example%.example}"; \
		if [ -e "$$env_file" ]; then \
			printf "$(YELLOW_COLOR)✓ $$env_file already exists, overwritting$(DEFAULT_COLOR)\\n"; \
		fi; \
		cp "$$path_to_env_example" "$$env_file"; \
		printf "$(GREEN_COLOR)✓ Created $$env_file$(DEFAULT_COLOR)\\n"; \
	done

# ---- Local services with containerized databases ----

dev-databases: secrets
	@$(call print,$(GREEN_COLOR),[DATABASES] Starting PostgreSQL and pgvector...)
	@$(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) up -d pgsql pgvector >/dev/null
	@attempt=1; until $(CONTAINER_CMD) exec pgsql pg_isready -U "$(POSTGRES_USER)" -d postgres >/dev/null 2>&1; do \
		if [ "$$attempt" -ge 60 ]; then \
			$(call print,$(RED_COLOR),[DATABASES] PostgreSQL did not become ready within 60 seconds.); \
			$(DEV_COMPOSE) ps pgsql; exit 1; \
		fi; \
		attempt=$$((attempt + 1)); sleep 1; \
	done
	@attempt=1; until $(CONTAINER_CMD) exec pgvector pg_isready -U "$(POSTGRES_USER)" -d postgres >/dev/null 2>&1; do \
		if [ "$$attempt" -ge 60 ]; then \
			$(call print,$(RED_COLOR),[DATABASES] pgvector did not become ready within 60 seconds.); \
			$(DEV_COMPOSE) ps pgvector; exit 1; \
		fi; \
		attempt=$$((attempt + 1)); sleep 1; \
	done
	@$(call print,$(GREEN_COLOR),✓ [DATABASES] Local development databases are running and healthy👩🏻‍⚕️.)

check-service:
ifndef SERVICE
	$(error SERVICE is not set. Usage: make $(firstword $(MAKECMDGOALS)) SERVICE=<service-name>)
endif
ifeq ($(wildcard $(SERVICES_DIR)/$(SERVICE)),)
	$(error Unknown service '$(SERVICE)'. Available: $(notdir $(wildcard $(SERVICES_DIR)/*)))
endif

# SERVICE is passed to Compose locally or through SSH, so accept only simple
# Compose service names before starting containers or restarting the VM.
check-compose-service:
	@if [ -n "$$SERVICE" ]; then \
		case "$$SERVICE" in \
			[!a-z]*|*[!a-z0-9-]*) \
				printf "Invalid Compose service name: %s\n" "$$SERVICE"; exit 2 ;; \
		esac; \
	fi


# The backend stays on the host. QEMU forwards the VM's database ports to
# localhost, matching the service Makefile's POSTGRES_HOST setting. Reuse the VM
# only when SSH and both database ports belong to the same QEMU process and
# that process does not also forward the gateway (the dev VM mode).
# QEMU's port forwards are fixed at boot, so any other mode needs a restart.
vm-databases:
	@if command -v lsof >/dev/null 2>&1 && $(VM_SSH) true >/dev/null 2>&1; then \
		ssh_pid=$$(lsof -nP -t -iTCP:$(VM_SSH_PORT) -sTCP:LISTEN); \
		pgsql_pid=$$(lsof -nP -t -iTCP:$(POSTGRES_PORT) -sTCP:LISTEN); \
		pgvector_pid=$$(lsof -nP -t -iTCP:$(AI_POSTGRES_PORT) -sTCP:LISTEN); \
	fi; \
	if [ -n "$$ssh_pid" ] && [ "$$ssh_pid" = "$$pgsql_pid" ] && [ "$$ssh_pid" = "$$pgvector_pid" ] && \
		! lsof -nP -a -p "$$ssh_pid" -iTCP:$(GATEWAY_HTTPS_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
		$(call print,$(GREEN_COLOR),[VM] Reusing VM with database ports forwarded.); \
		$(MAKE) --no-print-directory vm-sync; \
	else \
		$(call print,$(CYAN_COLOR),[VM] Restarting VM with database ports forwarded...); \
		$(MAKE) --no-print-directory stop-vm && \
		$(MAKE) --no-print-directory launch-vm VM_NETWORK_MODE=local-backend; \
	fi
	@$(VM_SSH) 'cd "$(VM_REMOTE_DIR)" && $(VM_REMOTE_ENV) make dev-databases SECRETS_MODE=validate'

run: check-service vm-databases
	@$(call print,$(CYAN_COLOR),[SERVICE] Running $(SERVICE) locally with VM databases...)
	@$(MAKE) -C $(SERVICES_DIR)/$(SERVICE) ensure-databases -s
	@$(MAKE) -C $(SERVICES_DIR)/$(SERVICE) run -s

# Run the worker in the existing AI Processing container inside the VM.
summarize: launch-vm
	@$(VM_SSH) 'cd "$(VM_REMOTE_DIR)" && $(PROD_COMPOSE) $(COMPOSE_PROFILES_ALL) exec -T ai-processing python -m src.worker'

# Stream the helper from the host so stopping does not require a VM sync or rebuild.
stop-summarize:
	@$(VM_SSH) 'docker exec -i ai-processing python -' < shared/script/stop_summarize.py

#service testing
test: check-service vm-databases
	@$(call print,$(CYAN_COLOR),[SERVICE] $(SERVICE) -> make $@)
	@$(MAKE) -C $(SERVICES_DIR)/$(SERVICE) $@ -s

#service development tools
migration upgrade downgrade status shell: check-service vm-databases
	@$(call print,$(CYAN_COLOR),[SERVICE] $(SERVICE) -> make $@)
	@$(MAKE) -C $(SERVICES_DIR)/$(SERVICE) ensure-databases -s
	@$(MAKE) -C $(SERVICES_DIR)/$(SERVICE) $@ -s

sync lint typecheck clear-cache reinstall: check-service
	@$(call print,$(CYAN_COLOR),[SERVICE] $(SERVICE) -> make $@)
	@$(MAKE) -C $(SERVICES_DIR)/$(SERVICE) $@ -s

list-services:
	@$(call print,$(BLUE_COLOR),[SERVICES] Available services:)
	@ls $(SERVICES_DIR)

# ============================================================================ #
#                                  DOCKER                                      #
# ============================================================================ #

# Create shared networks outside either Compose project. Neither project's
# `down` can remove an external network while the other still needs it.
shared-networks:
	@$(CONTAINER_CMD) network inspect "$(DOMAIN)-edge" >/dev/null 2>&1 || $(CONTAINER_CMD) network create "$(DOMAIN)-edge" >/dev/null
	@$(CONTAINER_CMD) network inspect "$(DOMAIN)-backend" >/dev/null 2>&1 || $(CONTAINER_CMD) network create "$(DOMAIN)-backend" >/dev/null

# Start the application stack, or one service and its dependencies.
# --wait returns once every service with a healthcheck is healthy, and fails if
# one never gets there: the success message below can then be trusted.
docker-app: check-compose-service secrets shared-networks
	@if [ -n "$$SERVICE" ]; then \
		$(call print,$(GREEN_COLOR),[DOCKER] Starting $$SERVICE and its dependencies in dev mode...); \
		$(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) up -d --wait --build "$$SERVICE"; \
	else \
		$(call print,$(GREEN_COLOR),[DOCKER] Starting all services in dev mode...); \
		$(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) up -d --wait --build; \
	fi
	@$(call print,$(GREEN_COLOR),✓ [DOCKER] $(NAME) development environment started successfully! 🥳🥳🥳)
	@$(call print,$(GREEN_COLOR),  Open https://localhost:$(GATEWAY_HTTPS_PORT))

docker: docker-app
	@if [ -z "$$SERVICE" ]; then $(MAKE) --no-print-directory monitoring-up SECRETS_MODE=validate; fi


# Build and run production Compose in the current environment. The prod target
# invokes this from inside the VM after selecting production port forwarding.
# Detached and waiting, like `make docker`: the command ends once the stack is
# healthy, and the logs stay available through `make logs`.
prod-docker: secrets shared-networks
	@$(call print,$(GREEN_COLOR),[DOCKER] Starting all services in production mode...)
	$(PROD_COMPOSE) $(COMPOSE_PROFILES_ALL) build --no-cache && \
	$(PROD_COMPOSE) $(COMPOSE_PROFILES_ALL) up -d --wait
	@$(call print,$(GREEN_COLOR),✓ [DOCKER] $(NAME) production environment started successfully! 🥳🥳🥳)
	@$(call print,$(GREEN_COLOR),  Open https://localhost:$(GATEWAY_HTTPS_PORT))
	@$(MAKE) --no-print-directory monitoring-up SECRETS_MODE=validate

# ============================================================================ #
#                                  DOCKER TOOLS CMDS                           #
# ============================================================================ #

#Follow logs
logs:
ifndef SERVICE
	@$(call print,$(CYAN_COLOR),[DOCKER] Following logs for all services...)
	$(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) logs -f
else
	@$(call print,$(CYAN_COLOR),[DOCKER] Following logs for $(SERVICE)...)
	$(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) logs $(SERVICE) -f
endif

#Stop containers
down:
	@$(call print,$(CYAN_COLOR),[DOCKER] Stopping $(NAME)...)
	@$(DEV_COMPOSE) $(COMPOSE_CLEAN_PROFILES_ALL) down
	@$(call print,$(GREEN_COLOR),[DOCKER] $(NAME) is down.)

ps:
	@$(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) ps

re: clean docker

#Stop and remove the images
clean:
	@$(call print,$(CYAN_COLOR),[DOCKER] Stopping development stack and removing images...)
	@$(DEV_COMPOSE) $(COMPOSE_CLEAN_PROFILES_ALL) \
		down --rmi all
	@$(call print,$(GREEN_COLOR),[DOCKER] Project images removing complete.)

#Remove persistent database volumes
reset-db:
	@$(call print,$(CYAN_COLOR),[DOCKER] Resetting database volumes...)
	@$(DEV_COMPOSE) $(COMPOSE_CLEAN_PROFILES_ALL) \
		down --volumes
	@$(call print,$(GREEN_COLOR),[DOCKER] Database resetting complete.)

#Confirm before removing only the database volumes and project images.
fclean:
	@printf "‼️🚨‼️Reset PostgreSQL and pgvector data, and remove project images? [y/N] "; read -r confirm; \
	case "$$confirm" in \
		[yY]|[yY][eE][sS]) \
			$(DEV_COMPOSE) $(COMPOSE_CLEAN_PROFILES_ALL) down --volumes --rmi all; \
			$(call print,$(GREEN_COLOR),[DOCKER] Database data and project images removed.) ;; \
		*) $(call print,$(YELLOW_COLOR),[DOCKER] Cleanup cancelled.) ;; \
	esac


# ============================================================================ #
#                                  VM DEVELOPMENT                              #
# ============================================================================ #

all:
	@test -z "$(SERVICE)" || { printf '[ALL] Unset SERVICE to start the full stack.\n' >&2; exit 2; }
	@if [ ! -s "$(NEWS_API_KEY)" ]; then \
		printf '$(YELLOW_COLOR)[WARNING] NewsAPI key missing or empty: %s. NewsAPI ingestion will be unavailable.$(DEFAULT_COLOR)\n' "$(NEWS_API_KEY)"; \
	fi
	@vm_present=false; \
	for disk in "$(VM_DIR)"/ubuntu-server-cloud-*.qcow2; do \
		if [ -f "$$disk" ]; then vm_present=true; break; fi; \
	done; \
	if [ "$$vm_present" = false ]; then \
		$(MAKE) --no-print-directory create-vm; \
	fi
	@$(MAKE) --no-print-directory vm-full-stack
	@sleep 3
	@$(MAKE) --no-print-directory ingest-vm
	@sleep 3
	@$(MAKE) --no-print-directory ollama
	@sleep 3
	@$(MAKE) --no-print-directory summarize




# Recreate only the current guest's disk and boot state, preserving VM_DIR.
create-vm:
	@vm_dir="$(VM_DIR)"; \
	if [ -z "$$vm_dir" ]; then printf 'VM_DIR must not be empty.\n'; exit 1; fi; \
	printf "‼️🚨‼️Recreate the current guest in %s? Its disk, database data, first-boot files and firmware state will be deleted. Cached images and unrelated files are kept. [y/N] " "$$vm_dir"; read -r confirm; \
	case "$$confirm" in \
		[yY]|[yY][eE][sS]) \
			$(MAKE) --no-print-directory stop-vm VM_DIR="$$vm_dir" || exit $$?; \
			$(VM_QEMU_ENV) VM_DIR="$$vm_dir" $(VM_SCRIPT) --reset-state || exit $$?; \
			ssh-keygen -R "[127.0.0.1]:$(VM_SSH_PORT)" >/dev/null 2>&1 || true; \
			ssh-keygen -R "[localhost]:$(VM_SSH_PORT)" >/dev/null 2>&1 || true; \
			$(MAKE) --no-print-directory launch-vm VM_DIR="$$vm_dir" || exit $$?; \
			$(call print,$(GREEN_COLOR),✓ [VM] Fresh VM provisioned and synced. It is running.) ;; \
		*) $(call print,$(YELLOW_COLOR),[VM] Recreate cancelled.); exit 1 ;; \
	esac

# Start the existing VM only when SSH cannot already reach it. QEMU's network
# forwarding mode is selected at boot, so run `make stop-vm` before changing
# VM_NETWORK_MODE between dev and prod.
launch-vm:
	@if $(VM_SSH) true >/dev/null 2>&1; then \
		$(call print,$(GREEN_COLOR),[VM] Already running; syncing the project.); \
	else \
		$(call print,$(GREEN_COLOR),[VM] Starting in $(VM_NETWORK_MODE) mode...); \
		$(VM_QEMU_ENV) $(VM_SCRIPT); \
	fi
	@$(MAKE) --no-print-directory vm-sync

# Prepare the VM as usual, then replace this recipe shell with an interactive
# SSH session. Exit the session with `exit` to return to the host terminal.
# Warning: the modifications inside vm will NOT be synched to host!!
# So dont do make secrets and change only files on host then sync
connect-vm: launch-vm
	@$(call print,$(CYAN_COLOR),[VM] Opening interactive SSH session. Use exit to return to the host.)
	@$(VM_SSH_TTY)

# Wait for both the SSH service and cloud-init. Cloud-init installs Docker and
# Make on a fresh guest, so Docker commands must not run before this completes.
vm-wait:
	@attempt=1; until $(VM_SSH) true >/dev/null 2>&1; do \
		if [ "$$attempt" -gt 60 ]; then \
			printf "$(RED_COLOR)[VM] SSH did not become ready within 60 seconds.$(DEFAULT_COLOR)\\n"; exit 1; \
		fi; \
		printf "$(CYAN_COLOR)[VM] Waiting for SSH (%s/60)...$(DEFAULT_COLOR)\\n" "$$attempt"; \
		attempt=$$((attempt + 1)); sleep 1; \
	done
	@$(call print,$(CYAN_COLOR),[VM] Waiting for cloud-init...)
	@$(VM_SSH) 'cloud-init status --wait; cloud_status=$$?; \
		if [ "$$cloud_status" -eq 2 ]; then \
			echo "[VM] cloud-init completed with recoverable errors; inspect cloud-init status --long if provisioning looks incomplete."; \
		elif [ "$$cloud_status" -ne 0 ]; then \
			exit "$$cloud_status"; \
		fi'

# Copy host source into the VM. Storage directories are excluded so VM disks
# and host backups stay on the host. This intentionally copies .env and the
# project's local secret files; the VM is a trusted development environment.
vm-sync: secrets vm-wait
	@$(VM_SSH) 'mkdir -p "$(VM_REMOTE_DIR)"'
	@$(call print,$(CYAN_COLOR),[VM] Synchronizing project files...)
	@rsync -az --progress \
		--exclude 'vm/' \
		--exclude 'vm-restore/' \
		--exclude 'backups/' \
		--exclude '/backup-extract-*/' \
		--exclude '/shared/secrets/backup_password' \
		--exclude '.git/' \
		--exclude '.venv/' \
		--exclude 'node_modules/' \
		--exclude '__pycache__/' \
		--exclude '.pytest_cache/' \
		--exclude '.mypy_cache/' \
		-e '$(VM_RSYNC_SSH)' \
		./ $(VM_USERNAME)@127.0.0.1:$(VM_REMOTE_DIR)/
	@$(call print,$(GREEN_COLOR),✓ [VM] Project synchronized.)

stop-vm:
	@if ! command -v lsof >/dev/null 2>&1; then \
		$(call print,$(RED_COLOR),[VM] lsof is required to verify that QEMU has stopped.); exit 1; \
	fi; \
	vm_pid=$$(lsof -nP -t -iTCP:$(VM_SSH_PORT) -sTCP:LISTEN); \
	if [ -z "$$vm_pid" ]; then \
		$(call print,$(YELLOW_COLOR),[VM] No VM is listening on SSH port $(VM_SSH_PORT).); \
	elif ! lsof -nP -a -p "$$vm_pid" "$(VM_DIR)"/ubuntu-server-cloud-*.qcow2 >/dev/null 2>&1; then \
		$(call print,$(RED_COLOR),[VM] Port $(VM_SSH_PORT) is not held by the configured VM disk.); exit 1; \
	elif ! $(VM_SSH) true >/dev/null 2>&1; then \
		$(call print,$(RED_COLOR),[VM] SSH is unreachable but QEMU still holds port $(VM_SSH_PORT).); exit 1; \
	else \
		$(call print,$(CYAN_COLOR),[VM] Requesting clean guest shutdown...); \
		$(VM_SSH) 'sudo poweroff' >/dev/null 2>&1 || true; \
		attempt=0; while kill -0 "$$vm_pid" 2>/dev/null; do \
			if [ "$$attempt" -ge 60 ]; then \
				$(call print,$(RED_COLOR),[VM] QEMU did not exit within 60 seconds.); exit 1; \
			fi; \
			attempt=$$((attempt + 1)); sleep 1; \
		done; \
		$(call print,$(GREEN_COLOR),✓ [VM] Guest stopped.); \
	fi

# Use only for diagnosing early boot or cloud-init failures. It keeps QEMU in
# the foreground and does not attempt automatic rsync or shutdown.
debug-create-vm:
	@$(VM_QEMU_ENV) VM_DEBUG=1 $(VM_SCRIPT)

# QEMU's port forwards are fixed at boot. Each VM stack target restarts in
# development mode so the gateway, database, and Grafana ports are forwarded.
vm-full-stack:
	@test -z "$$SERVICE" || { printf '[VM] Use vm-service SERVICE=<name> for one service.\n' >&2; exit 2; }
	@$(call print,$(CYAN_COLOR),[VM] Starting the application and monitoring in the VM...)
	@$(MAKE) --no-print-directory stop-vm
	@$(MAKE) --no-print-directory launch-vm VM_NETWORK_MODE=dev
	@$(VM_SSH) 'cd "$(VM_REMOTE_DIR)" && $(VM_REMOTE_ENV) make docker SECRETS_MODE=validate SERVICE='

vm-app:
	@test -z "$$SERVICE" || { printf '[VM] Use vm-service SERVICE=<name> for one service.\n' >&2; exit 2; }
	@$(call print,$(CYAN_COLOR),[VM] Starting only the application stack in the VM...)
	@$(MAKE) --no-print-directory stop-vm
	@$(MAKE) --no-print-directory launch-vm VM_NETWORK_MODE=dev
	@$(VM_SSH) 'cd "$(VM_REMOTE_DIR)" && $(VM_REMOTE_ENV) make monitoring-down && $(VM_REMOTE_ENV) make docker-app SECRETS_MODE=validate SERVICE='

vm-service: check-compose-service
	@test -n "$$SERVICE" || { printf '[VM] Set SERVICE=<name> to choose a Compose service.\n' >&2; exit 2; }
	@$(call print,$(CYAN_COLOR),[VM] Starting $(SERVICE) and its dependencies in the VM...)
	@$(MAKE) --no-print-directory stop-vm
	@$(MAKE) --no-print-directory launch-vm VM_NETWORK_MODE=dev
	@$(VM_SSH) 'cd "$(VM_REMOTE_DIR)" && $(VM_REMOTE_ENV) make docker-app SECRETS_MODE=validate SERVICE=$(SERVICE)'

# Forward existing Docker-oriented Make targets into the synchronized VM.
$(addsuffix -vm,$(VM_DOCKER_TARGETS)): launch-vm
	@$(call print,$(CYAN_COLOR),[VM] Running make $(patsubst %-vm,%,$@) in the guest...)
	@$(VM_SSH) 'cd "$(VM_REMOTE_DIR)" && $(VM_REMOTE_ENV) make $(patsubst %-vm,%,$@) SECRETS_MODE=validate $(if $(SERVICE),SERVICE=$(SERVICE),)'

# Production forwards the gateway and host-loopback Grafana. It
# stops a development-mode VM first because QEMU forwarding is fixed at boot.
prod:
	@$(MAKE) --no-print-directory stop-vm
	@$(MAKE) --no-print-directory launch-vm VM_NETWORK_MODE=prod
	@$(VM_SSH) 'cd "$(VM_REMOTE_DIR)" && $(VM_REMOTE_ENV) make prod-docker SECRETS_MODE=validate'

# fclean asks for confirmation in the guest, so force a terminal allocation.
fclean-vm: launch-vm
	@$(VM_SSH_TTY) 'cd "$(VM_REMOTE_DIR)" && make fclean'


# ============================================================================ #
#                              MAKEFILE SETTING                                #
# ============================================================================ #

#not print command
.SILENT:

#Delete target files if command fails
.DELETE_ON_ERROR:

.PHONY: clean fclean logs down reset-db secrets check-service check-compose-service \
		vm-databases \
		frontend frontend-install frontend-build frontend-test \
		dev dev-databases docker docker-app vm-full-stack vm-app vm-service sync run summarize stop-summarize migration upgrade downgrade \
		test lint typecheck shell list-services status clear-cache reinstall \
		up build ps logs init-env create-vm launch-vm stop-vm debug-create-vm \
		shared-networks \
		connect-vm vm-wait vm-sync prod prod-docker fclean-vm $(addsuffix -vm,$(VM_DOCKER_TARGETS))
