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

.PHONY: check-news-api-secret ingest logs test

check-news-api-secret:
	@if [ ! -r "$(NEWS_API_SECRET)" ] || [ ! -s "$(NEWS_API_SECRET)" ]; then \
		$(call print,$(RED_COLOR),[SECRETS] Add your NewsAPI key to $(NEWS_API_SECRET).); \
		exit 1; \
	fi

run: check-news-api-secret

ingest:
	@if ! command -v curl >/dev/null 2>&1; then \
		$(call print,$(RED_COLOR),Error: curl is required to trigger ingestion.); \
		exit 1; \
	fi
	@$(call print,$(CYAN_COLOR),[CONTENT MANAGEMENT] Ingesting articles...)
	@curl --fail-with-body --silent --show-error --connect-timeout 5 \
		--request POST \
		--header "Accept: application/json" \
		"$(CONTENT_MANAGEMENT_URL)/internal/v1/ingestion-runs"
	@printf "\n"
