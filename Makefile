# ============================================================
# transcendence/Makefile
# ------------------------------------------------------------
# Pure dispatcher — no build logic lives here. Forwards whatever
# target was invoked down to the chosen service's own Makefile.
# ============================================================

################################## VARIABLES ###################################

FRONTEND_DIR := srcs/frontend
SERVICES_DIR := srcs/services
COMPOSE      := docker compose

################################### INCLUDES ###################################

include shared/mk/colors.mk

##################################### RULES ####################################

.PHONY: frontend frontend-install frontend-build status clear-cache \
		sync run migration upgrade downgrade test lint typecheck shell list-services \
		up down build ps logs

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

# ---- Whole-stack orchestration (via docker compose) ----
up:
	@$(call print,$(GREEN_COLOR),[DOCKER] Starting all services...)
	$(COMPOSE) up -d

down:
	@$(call print,$(YELLOW_COLOR),[DOCKER] Stopping all services...)
	$(COMPOSE) down

build:
	@$(call print,$(BLUE_COLOR),[DOCKER] Building all services...)
	$(COMPOSE) build

ps:
	@$(call print,$(BLUE_COLOR),[DOCKER] Container status:)
	$(COMPOSE) ps

logs:
ifndef SERVICE
	@$(call print,$(CYAN_COLOR),[DOCKER] Following logs for all services...)
	$(COMPOSE) logs -f
else
	@$(call print,$(CYAN_COLOR),[DOCKER] Following logs for $(SERVICE)...)
	$(COMPOSE) logs -f $(SERVICE)
endif
