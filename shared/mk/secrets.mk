SECRET_DIR := shared/secrets

# Password string-based secrets
SECRET_FILES := \
	$(SECRET_DIR)/postgres_password

# JWT keys
JWT_PRIVATE_KEY := $(SECRET_DIR)/jwt_private_key
JWT_PUBLIC_KEY  := $(SECRET_DIR)/jwt_public_key

# Provider credentials are supplied by developers/operators and never generated.
NEWS_API_KEY := $(SECRET_DIR)/news_api_key


# VM commands validate the host-owned files copied by vm-sync.
# Direct host commands retain the existing generation behavior.
SECRETS_MODE ?= generate

.PHONY: secrets secrets-check secrets-banner secrets-dir secrets-random secrets-jwt-keys \
		news-api-secret-check

ifeq ($(SECRETS_MODE),validate)
secrets: secrets-check
else ifeq ($(SECRETS_MODE),generate)
secrets: secrets-banner secrets-random secrets-jwt-keys
	@$(call print,$(GREEN_COLOR),✓ All secrets are ready.)
else
$(error SECRETS_MODE must be generate or validate)
endif

secrets-check:
	@for secret in $(SECRET_FILES) $(JWT_PRIVATE_KEY) $(JWT_PUBLIC_KEY); do \
		if [ ! -r "$$secret" ] || [ ! -s "$$secret" ]; then \
			printf '[SECRETS] Missing, empty, or unreadable file: %s. Run make vm-sync on the host.\n' "$$secret" >&2; \
			exit 1; \
		fi; \
	done

secrets-banner:
	@printf "$(CYAN_COLOR)🔍🔍🔍 Verifying and generating secrets at current directory 🕵️$(DEFAULT_COLOR)\n"

# --- Secret directory ---
secrets-dir:
	@mkdir -p "$(SECRET_DIR)"


# --- Password/String secrets ---
secrets-random: | secrets-dir
	@for secret in $(SECRET_FILES); do \
		if [ ! -s "$$secret" ]; then \
			printf "$(YELLOW_COLOR)㊙️ Generating $$secret...$(DEFAULT_COLOR)\n"; \
			openssl rand -base64 32 | tr -d '=+/' | head -c 32 > "$$secret"; \
			printf "$(GREEN_COLOR)✓ $$secret generated$(DEFAULT_COLOR)\n"; \
		else \
			printf "$(GREEN_COLOR)✓ $$secret already exists, skipping ㊙️$(DEFAULT_COLOR)\n"; \
		fi; \
	done

# --- Externally supplied provider credentials ---
news-api-secret-check: | secrets-dir
	@if [ ! -r "$(NEWS_API_KEY)" ] || [ ! -s "$(NEWS_API_KEY)" ]; then \
		printf '$(RED_COLOR)[SECRETS] Add your NewsAPI key to $(NEWS_API_KEY).$(DEFAULT_COLOR)\n' >&2; \
		exit 1; \
	fi

# --- JWT keys ---
secrets-jwt-keys: | secrets-dir
	@if [ ! -s "$(JWT_PRIVATE_KEY)" ]; then \
		printf "$(YELLOW_COLOR)㊙️ Generating $(JWT_PRIVATE_KEY)...$(DEFAULT_COLOR)\n"; \
		openssl genrsa -out "$(JWT_PRIVATE_KEY)" 2048; \
		printf "$(GREEN_COLOR)✓ Private key generated$(DEFAULT_COLOR)\n"; \
	else \
		printf "$(GREEN_COLOR)✓ $(JWT_PRIVATE_KEY) already exists, skipping ㊙️$(DEFAULT_COLOR)\n"; \
	fi
	@if [ ! -s "$(JWT_PUBLIC_KEY)" ]; then \
		printf "$(YELLOW_COLOR)🔑 Generating $(JWT_PUBLIC_KEY)...$(DEFAULT_COLOR)\n"; \
		openssl rsa -in "$(JWT_PRIVATE_KEY)" -pubout -out "$(JWT_PUBLIC_KEY)"; \
		printf "$(GREEN_COLOR)✓ Public key generated$(DEFAULT_COLOR)\n"; \
	else \
		printf "$(GREEN_COLOR)✓ $(JWT_PUBLIC_KEY) already exists, skipping 🔑$(DEFAULT_COLOR)\n"; \
	fi
