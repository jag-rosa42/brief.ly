################################## VARIABLES ###################################

ROOT_DIR := $(shell git rev-parse --show-toplevel)
PORT      = $(CONTENT_MANAGEMENT_PORT)


include $(ROOT_DIR)/shared/mk/service.mk
include $(ROOT_DIR)/.env

CONTENT_MANAGEMENT_URL ?= http://$(HOST):$(PORT)
NEWS_API_SECRET := $(ROOT_DIR)/shared/secrets/news_api_key

# ======== TMP TEST WITH LOGS ===============
# TODO: Format loggers

TEST_DIR        ?= tests
LEVEL ?= info
PYTEST_LOG_OPTS ?= \
	-o log_cli=true \
	--log-cli-level=$(LEVEL) \
	--log-cli-format='%(asctime)s [%(levelname)s] %(name)s: %(message)s' \
	--log-cli-date-format='%H:%M:%S'

# usage: make test-tmp TEST_DIR=tests/s01 LEVEL=ERROR
test-tmp: check-env
	$(RUN) pytest $(TEST_DIR) $(PYTEST_LOG_OPTS)

# ===========================================

##################################### RULES ####################################

.PHONY: ingest logs test

ingest: check-env
	@$(call print,$(CYAN_COLOR),[CONTENT MANAGEMENT] Ingesting articles...)
	@uv run python scripts/trigger_ingestion.py --url "$(CONTENT_MANAGEMENT_URL)" \
		--secret-file "$(NEWS_API_SECRET)"
