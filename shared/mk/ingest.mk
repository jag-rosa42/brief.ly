# Warn without blocking startup: ingestion can use providers other than NewsAPI.
ingest-check-key:
	@if [ ! -s "$(NEWS_API_KEY)" ]; then \
		printf '$(YELLOW_COLOR)[WARNING] NewsAPI key missing or empty: %s. NewsAPI ingestion will be unavailable.$(DEFAULT_COLOR)\n' "$(NEWS_API_KEY)"; \
	fi

ingest:
	@$(MAKE) -C $(SERVICES_DIR)/content-management $@ -s

# Reset AI assessments so the worker can process the same article content again.
clear-summaries-vm:
	@printf 'Delete all article assessments (including rejection decisions) and topic summaries in the VM? Article content is preserved. Stop the AI worker first. [y/N] '; \
	read -r confirm; \
	case "$$confirm" in \
		[yY]|[yY][eE][sS]) \
			printf '%s\n' \
				'BEGIN;' \
				'DELETE FROM article_summaries;' \
				'DELETE FROM topic_summaries;' \
				'COMMIT;' \
				'SELECT count(*) AS articles_preserved FROM normalized_articles;' \
				'SELECT count(*) AS assessments_remaining FROM article_summaries;' | \
				$(VM_SSH) 'docker exec -i pgsql sh -c '\''exec psql -v ON_ERROR_STOP=1 -U "$$POSTGRES_USER" -d content_management_db'\''' ;; \
		*) printf '[CONTENT MANAGEMENT] Summary reset cancelled.\n' ;; \
	esac

# Content Management has no published host port in Compose. Run the same HTTP
# client inside its container, where both the service and its secret are present.
ingest-docker:
	@if ! $(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) exec -T content-management true >/dev/null 2>&1; then \
		printf '[CONTENT MANAGEMENT] Container is not running. Start it with make docker SERVICE=content-management (or make vm-service SERVICE=content-management).\n' >&2; \
		exit 1; \
	fi
	@$(call print,$(CYAN_COLOR),[CONTENT MANAGEMENT] Ingesting articles in Docker...)
	@$(DEV_COMPOSE) $(COMPOSE_PROFILES_ALL) exec -T content-management python scripts/trigger_ingestion.py \
		--url http://127.0.0.1:8000 --secret-file /run/secrets/news_api_key

# Do not start a VM just to trigger ingestion. Synchronize the client only after
# verifying that the caller already has a running guest.
ingest-vm:
	@if ! $(VM_SSH) true >/dev/null 2>&1; then \
		printf '[VM] VM is not running or SSH is unavailable. Start it with make vm-service SERVICE=content-management.\n' >&2; \
		exit 1; \
	fi
	@$(MAKE) --no-print-directory vm-sync
	@$(call print,$(CYAN_COLOR),[VM] Triggering Content Management ingestion in the guest...)
	@$(VM_SSH) 'cd "$(VM_REMOTE_DIR)" && $(VM_REMOTE_ENV) make ingest-docker SECRETS_MODE=validate'

# Clear article data in both service databases before a fresh ingestion.
clear-articles-vm:
	@printf 'Delete all articles, generated summaries, and saved article snapshots in the VM? Users, sources, and topics are preserved. [y/N] '; \
	read -r confirm; \
	case "$$confirm" in \
		[yY]|[yY][eE][sS]) \
			printf '%s\n' \
				'BEGIN;' \
				'DELETE FROM saved_article;' \
				'COMMIT;' \
				'SELECT count(*) AS remaining_saved_articles FROM saved_article;' | \
				$(VM_SSH) 'docker exec -i pgsql sh -c '\''exec psql -v ON_ERROR_STOP=1 -U "$$POSTGRES_USER" -d personalization_db'\''' || exit 1; \
			printf '%s\n' \
				'BEGIN;' \
				'DELETE FROM article_summaries;' \
				'DELETE FROM normalized_articles;' \
				'DELETE FROM topic_summaries;' \
				'COMMIT;' \
				'SELECT count(*) AS remaining_articles FROM normalized_articles;' | \
				$(VM_SSH) 'docker exec -i pgsql sh -c '\''exec psql -v ON_ERROR_STOP=1 -U "$$POSTGRES_USER" -d content_management_db'\''' ;; \
		*) printf '[CONTENT MANAGEMENT] Article deletion cancelled.\n' ;; \
	esac

.PHONY: ingest-check-key ingest ingest-docker ingest-vm clear-articles-vm clear-summaries-vm
