# ============================================================
# transcendence/shared/mk/service.mk
# ------------------------------------------------------------
# Shared recipes, included by every service's own Makefile.
# Never invoked directly — always included, never called with
# `make -f service.mk` on its own.
# ============================================================

################################### VARIABLES ##################################
# Fixed/calculated variables configuration
SHELL        := /bin/bash
ROOT_DIR     := $(shell git rev-parse --show-toplevel)
SERVICE_DIR  := $(CURDIR)
ENV_FILE     := ${SERVICE_DIR}/.env

# Default variables that users may override
RUN          ?= uv run
UV           ?= uv
APP          ?= src.main:app
HOST         ?= 127.0.0.1

################################### INCLUDES ###################################

include $(ROOT_DIR)/.env
-include $(ENV_FILE)
include $(ROOT_DIR)/shared/mk/colors.mk
export

##################################### UTILS ####################################

check-env:
	@if [[ ! -f "$(ENV_FILE)" ]]; then \
		$(call print,$(RED_COLOR),Error: .env file not found at $(ENV_FILE)); \
		exit 1; \
	fi

##################################### RULES ####################################

.PHONY: run sync migration upgrade downgrade test lint typecheck shell

run: check-env
	@$(call print,$(GREEN_COLOR),[RUN] Starting $(PROJECT_NAME)...)
	$(RUN) uvicorn $(APP) --reload --host $(HOST) --port $(PORT)

sync: check-env
	@$(call print,$(CYAN_COLOR),[SYNC] Syncing dependencies for $(PROJECT_NAME)...)
	$(UV) sync
	@$(call print,$(GREEN_COLOR),[SYNC] Dependencies synchronized for $(PROJECT_NAME).)

migration: check-env
ifndef MESSAGE
	$(error MESSAGE is not set. Usage: make migration SERVICE=identity MESSAGE="add users table")
endif
	@$(call print,$(BLUE_COLOR),[MIGRATION] Creating migration for $(PROJECT_NAME)...)
	$(RUN) alembic revision --autogenerate -m "$(MESSAGE)"

upgrade: check-env
	@$(call print,$(GREEN_COLOR),[UPGRADE] Applying migrations for $(PROJECT_NAME)...)
	$(RUN) alembic upgrade $(or $(REVISION),head)

downgrade: check-env
	@$(call print,$(YELLOW_COLOR),[DOWNGRADE] Reverting migration for $(PROJECT_NAME)...)
	$(RUN) alembic downgrade $(or $(REVISION),-1)

test: check-env
	@$(call print,$(BLUE_COLOR),[TEST] Running tests for $(PROJECT_NAME)...)
	$(RUN) pytest

lint: check-env
	@$(call print,$(BLUE_COLOR),[LINT] Checking $(PROJECT_NAME)...)
	$(RUN) ruff check .

typecheck: check-env
	@$(call print,$(BLUE_COLOR),[TYPECHECK] Checking $(PROJECT_NAME)...)
	$(RUN) ty check

shell: check-env
	@$(call print,$(CYAN_COLOR),[SHELL] Opening Python shell for $(PROJECT_NAME)...)
	$(RUN) python
