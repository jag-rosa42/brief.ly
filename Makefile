# Pure dispatcher — no build logic lives here. Forwards whatever
# target was invoked down to the chosen service's own Makefile.

include .env
include shared/mk/colors.mk

NAME := Transcendence
.DEFAULT_GOAL := help

# ============================================================================ #
#                                     OS                                       #
# ============================================================================ #
OS := $(shell uname -s)

# ============================================================================ #
#                               VARIABLES & FLAGS                              #
# ============================================================================ #

MAKE_CMD ?= $(MAKE)
COMPOSE := podman compose
DEV_COMPOSE = $(COMPOSE) $(addprefix -f ,$(DEV_COMPOSE_FILE))
PROD_COMPOSE = $(COMPOSE) $(addprefix -f ,$(PROD_COMPOSE_FILE))
COMPOSE_PROFILES := frontend backend databases
COMPOSE_PROFILES_ALL := $(addprefix --profile ,$(COMPOSE_PROFILES))
COMPOSE_CLEAN_PROFILES_ALL := $(COMPOSE_PROFILES_ALL) --profile front-test

# ============================================================================ #
#                                DIRECTORIES                                   #
# ============================================================================ #

SRC_DIR := srcs
SECRET_DIR := shared/secrets/
FRONTEND_DIR := srcs/frontend
SERVICES_DIR := srcs/services

# ============================================================================ #
#                                  SOURCES                                     #
# ============================================================================ #

PROD_COMPOSE_FILE := compose.yaml
DEV_COMPOSE_FILE := compose.yaml compose.override.yaml
ENV_FILE := .env

#for mac OS
ifeq ($(OS),Darwin)
DEV_COMPOSE_FILE += compose.mac.yaml
endif



#============================================================================ #
#                                  SECRETS                                     #
# ============================================================================ #
 
SECRET_FILES := \
	$(SECRET_DIR)/postgres_password \
 
# ============================================================================ #
#                                  🫡HELP                                     #
# ============================================================================ #

help:
	@printf "\n$(BLUE_COLOR)🚀 $(NAME) — available commands$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 💻 Dev local ─────────────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(GREEN_COLOR)  Frontend$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) frontend                  $(CYAN_COLOR)Start the frontend locally$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) frontend-install          $(CYAN_COLOR)Install frontend dependencies$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) frontend-build            $(CYAN_COLOR)Build the frontend$(DEFAULT_COLOR)\n"
	@printf "$(GREEN_COLOR)  Databases$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) dev-databases             $(CYAN_COLOR)Start PostgreSQL and pgvector containers$(DEFAULT_COLOR)\n"
	@printf "$(GREEN_COLOR)  Backend$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) dev SERVICE=<name>        $(CYAN_COLOR)Run one backend service locally$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) test SERVICE=<name>        $(CYAN_COLOR)Run service tests locally$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) lint SERVICE=<name>        $(CYAN_COLOR)Lint a service locally$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) run SERVICE=<name>         $(CYAN_COLOR)Run a service locally$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) sync SERVICE=<name>        $(CYAN_COLOR)Synchronize service dependencies$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) typecheck SERVICE=<name>   $(CYAN_COLOR)Type-check a service locally$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) status SERVICE=<name>      $(CYAN_COLOR)Show service status$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) clear-cache SERVICE=<name> $(CYAN_COLOR)Clear service cache$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) migration SERVICE=<name>   $(CYAN_COLOR)Create a migration$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) upgrade SERVICE=<name>     $(CYAN_COLOR)Apply migrations$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) downgrade SERVICE=<name>   $(CYAN_COLOR)Revert migrations$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) list-services              $(CYAN_COLOR)List available backend services$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 🐳 Dev Docker ─────────────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(GREEN_COLOR)  Frontend$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) dev-docker SERVICE=frontend $(CYAN_COLOR)Run only the frontend$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) frontend-test             $(CYAN_COLOR)Run frontend tests in Docker$(DEFAULT_COLOR)\n"
	@printf "$(GREEN_COLOR)  Backend$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) dev-docker SERVICE=<name> $(CYAN_COLOR)Run one backend service with its database dependencies$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)    make$(YELLOW_COLOR) dev-docker                $(CYAN_COLOR)Run the complete development stack (frontend, backends, and databases)$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 🚀 Production ─────────────────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)  make$(YELLOW_COLOR) prod                        $(CYAN_COLOR)Build and run the complete production stack$(DEFAULT_COLOR)\n\n"
	@printf "$(ROSE_COLOR)── 📦 Shared container tools ────────────────────────────────────────────$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)  make$(YELLOW_COLOR) logs [SERVICE=<name>]        $(CYAN_COLOR)Follow container logs$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)  make$(YELLOW_COLOR) ps                           $(CYAN_COLOR)Show container status$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)  make$(YELLOW_COLOR) down                         $(CYAN_COLOR)Stop containers$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)  make$(YELLOW_COLOR) re                           $(CYAN_COLOR)Clean and rebuild the stack$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)  make$(YELLOW_COLOR) clean                        $(CYAN_COLOR)Stop containers, remove volumes and images$(DEFAULT_COLOR)\n"
	@printf "$(BLUE_COLOR)  make$(YELLOW_COLOR) secrets                      $(CYAN_COLOR)Create missing secrets$(DEFAULT_COLOR)\n\n"
 

# ============================================================================ #
#                                  LOCAL DEV (no Docker)                       #
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

# ---- Per-service dispatch (local dev, via uv) ----
run sync migration upgrade downgrade test lint typecheck shell status clear-cache:

ifndef SERVICE
	$(error SERVICE is not set. Usage: make $@ SERVICE=<service-name>)
endif
ifeq ($(wildcard $(SERVICES_DIR)/$(SERVICE)),)
	$(error Unknown service '$(SERVICE)'. Available: $(notdir $(wildcard $(SERVICES_DIR)/*)))
endif
	@$(call print,$(CYAN_COLOR),[SERVICE] $(SERVICE) -> make $@)
	@$(MAKE) -C $(SERVICES_DIR)/$(SERVICE) $@ -s

list-services:
	@$(call print,$(BLUE_COLOR),[SERVICES] Available services:)
	@ls $(SERVICES_DIR)

# ============================================================================ #
#                                  DEV-DOCKER                                  #
# ============================================================================ #

# Without SERVICE, start the complete development stack. With SERVICE, Compose
# starts only that service and its declared `depends_on` graph (its databases).
dev-docker: check-databases-volume secrets

ifeq ($(strip $(SERVICE)),)
	@$(call print,$(GREEN_COLOR),[DOCKER] Starting all services in dev mode...)
	$(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) up --build

else
	@$(call print,$(GREEN_COLOR),[DOCKER] Starting $(SERVICE) and its dependencies in dev mode...)
	@$(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) up --build $(SERVICE)
endif
	@$(call print,$(GREEN_COLOR),✓ [DOCKER] $(NAME) development environment started successfully! 🥳🥳🥳)

#check if DATABASES_VOLUME_DIR presents in .env file
check-databases-volume:
	@if [ -z "$(DATABASES_VOLUME_DIR)" ]; then \
		printf "DATABASES_VOLUME_DIR is not set. Add it to .env before starting containers.\\n" >&2; \
		exit 2; \
	fi
	@mkdir -p "$(DATABASES_VOLUME_DIR)/pgsql" "$(DATABASES_VOLUME_DIR)/pgvector"

#Generate missing secrets files
secrets:
	@printf "$(CYAN_COLOR)🔍🔍🔍 Verifying and generating secrets at current directory 🕵️$(DEFAULT_COLOR)\n"
	mkdir -p $(SECRET_DIR); \
	for secret in $(SECRET_FILES); do \
		if [ ! -s $$secret ]; then \
			printf "$(YELLOW_COLOR)㊙️ Generating $$secret...$(DEFAULT_COLOR)\n"; \
			openssl rand -base64 32 | tr -d '=+/' | head -c 32 > $$secret; \
			printf "$(GREEN_COLOR)✓ $$secret generated$(DEFAULT_COLOR)\n"; \
		else \
			printf "$(GREEN_COLOR)✓ $$secret already exists, skipping ㊙️$(DEFAULT_COLOR)\n"; \
		fi \
	done

# ============================================================================ #
#                                  PROD-DOCKER#
# ============================================================================ #

prod: check-databases-volume secrets
	@$(call print,$(GREEN_COLOR),[DOCKER] Starting all services in production mode...)
	$(PROD_COMPOSE) $(COMPOSE_PROFILES_ALL) build --no-cache && \
	$(PROD_COMPOSE) $(COMPOSE_PROFILES_ALL) up
	@$(call print,$(GREEN_COLOR),✓ [DOCKER] $(NAME) production environment started successfully! 🥳🥳🥳)


# ============================================================================ #
#                                  DOCKER-CMDS                                 #
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
	@$(DEV_COMPOSE) ps

re: clean dev-docker

#Stop and remove the volumes and images
clean:
	@$(call print,$(CYAN_COLOR),[DOCKER] Stopping development stack and removing volumes/images...)
	@$(DEV_COMPOSE) $(COMPOSE_CLEAN_PROFILES_ALL) \
		down --volumes --rmi all
	@$(call print,$(GREEN_COLOR),[DOCKER] Cleanup complete.)


# ============================================================================ #
#                              MAKEFILE SETTING                                #
# ============================================================================ #

#not print command
.SILENT:

#Delete target files if command fails
.DELETE_ON_ERROR:

.PHONY: clean logs down secrets \
		frontend frontend-install frontend-build frontend-test \
		dev dev-databases dev-docker sync run migration upgrade downgrade \
		test lint typecheck shell list-services status clear-cache \
		up build ps logs check-databases-volume
