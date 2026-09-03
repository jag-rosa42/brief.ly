################################## VARIABLES ###################################

ROOT_DIR := $(shell git rev-parse --show-toplevel)
PORT      = $(CONTENT_MANAGEMENT_PORT)


include $(ROOT_DIR)/shared/mk/service.mk
include $(ROOT_DIR)/.env

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

.PHONY: logs test
