ingest:
	@$(MAKE) -C $(SERVICES_DIR)/content-management $@ -s

# Content Management has no published host port in Compose. Run the same HTTP
# client inside its container, where both the service and its secret are present.
ingest-docker:
	@if ! $(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) exec -T content-management true >/dev/null 2>&1; then \
		printf '[CONTENT MANAGEMENT] Container is not running. Start it with make docker SERVICE=content-management (or make vm SERVICE=content-management).\n' >&2; \
		exit 1; \
	fi
	@$(call print,$(CYAN_COLOR),[CONTENT MANAGEMENT] Ingesting articles in Docker...)
	@$(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) exec -T content-management python scripts/trigger_ingestion.py \
		--url http://127.0.0.1:8000 --secret-file /run/secrets/news_api_key

# Do not start a VM just to trigger ingestion. Synchronize the client only after
# verifying that the caller already has a running guest.
ingest-vm:
	@if ! $(VM_SSH) true >/dev/null 2>&1; then \
		printf '[VM] VM is not running or SSH is unavailable. Start it with make vm SERVICE=content-management.\n' >&2; \
		exit 1; \
	fi
	@$(MAKE) --no-print-directory vm-sync
	@$(call print,$(CYAN_COLOR),[VM] Triggering Content Management ingestion in the guest...)
	@$(VM_SSH) 'cd "$(VM_REMOTE_DIR)" && $(VM_REMOTE_ENV) make ingest-docker SECRETS_MODE=validate'

.PHONY: ingest ingest-docker ingest-vm
