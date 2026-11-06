SECRET_DIR         := shared/secrets
CLIENT_SECRET_DIR  := $(SECRET_DIR)/services

# Service client secrets (ADR-0008): one per backend service that asks
# Identity for service tokens. Identity and that service both mount it.
# The client list: srcs/services/identity/src/infrastructure/oauth/service_clients.py
SERVICES_CLIENT_SECRET_FILES := \
	$(CLIENT_SECRET_DIR)/personalization_client_secret \
	$(CLIENT_SECRET_DIR)/morning_briefing_client_secret \
	$(CLIENT_SECRET_DIR)/ai_processing_client_secret

# Password string-based secrets, 32 random characters each
SECRET_FILES := \
	$(SECRET_DIR)/postgres_password \
	$(SERVICES_CLIENT_SECRET_FILES)

# JWT keys
JWT_PRIVATE_KEY := $(SECRET_DIR)/jwt_private_key
JWT_PUBLIC_KEY  := $(SECRET_DIR)/jwt_public_key

# Provider credentials are supplied by developers/operators and never generated.
NEWS_API_KEY := $(SECRET_DIR)/news_api_key

# The gateway's HTTPS identity (ADR-0006), a pair of files:
# - the certificate is public: the gateway sends it to every browser. It says
#   "this server is localhost" and holds the public key;
# - the private key stays secret: it proves the gateway owns that certificate.
# These filenames follow mkcert's default naming convention, so developers
# can use their own trusted certificates without renaming the files or changing the configuration.
CERTIFICATE_DIR      := $(SECRET_DIR)/certs
TLS_CERTIFICATE      := $(CERTIFICATE_DIR)/localhost.pem
TLS_PRIVATE_KEY      := $(CERTIFICATE_DIR)/localhost-key.pem


# VM commands validate the host-owned files copied by vm-sync.
# Direct host commands retain the existing generation behavior.
SECRETS_MODE ?= generate

.PHONY: secrets secrets-check secrets-banner secrets-dir secrets-random secrets-jwt-keys \
		secrets-provider-placeholders secrets-certs

ifeq ($(SECRETS_MODE),validate)
secrets: secrets-check
else ifeq ($(SECRETS_MODE),generate)
secrets: secrets-banner secrets-random secrets-jwt-keys secrets-provider-placeholders secrets-certs
	@$(call print,$(GREEN_COLOR),✓ Generated secrets and provider placeholders are ready.)
else
$(error SECRETS_MODE must be generate or validate)
endif

secrets-check:
	@for secret in $(SECRET_FILES) $(JWT_PRIVATE_KEY) $(JWT_PUBLIC_KEY) $(TLS_CERTIFICATE) $(TLS_PRIVATE_KEY); do \
		if [ ! -r "$$secret" ] || [ ! -s "$$secret" ]; then \
			printf '[SECRETS] Missing, empty, or unreadable file: %s. Run make vm-sync on the host.\n' "$$secret" >&2; \
			exit 1; \
		fi; \
	done

secrets-banner:
	@printf "$(CYAN_COLOR)🔍🔍🔍 Verifying and generating secrets at current directory 🕵️$(DEFAULT_COLOR)\n"

# --- Secret directory ---
secrets-dir:
	@mkdir -p "$(SECRET_DIR)" "$(CLIENT_SECRET_DIR)"


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
secrets-provider-placeholders: | secrets-dir
	@if [ ! -e "$(NEWS_API_KEY)" ]; then \
		install -m 600 /dev/null "$(NEWS_API_KEY)"; \
		printf "$(YELLOW_COLOR)[SECRETS] Created empty provider credential placeholder: $(NEWS_API_KEY).$(DEFAULT_COLOR)\n"; \
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

# --- Gateway TLS certificate ---
# Keep existing certificates, whether generated with mkcert or previously
# created. Otherwise, generate a self-signed certificate for localhost so the
# stack can start without manual setup. The browser will show a warning until
# the certificate is trusted (see README.docker.md).
# Subject Alternative Name (SAN) is required because modern browsers no longer
# rely on the Common Name (CN) alone to verify the certificate's hostname.
#
# OpenSSL options:
# -x509                        Generate a self-signed certificate.
# -newkey rsa:2048             Generate a new 2048-bit RSA private key.
# -nodes                       Do not encrypt the private key, so Traefik can
#                              read it without a password.
# -days 365                    Set the certificate's validity to 365 days.
# -subj "/CN=localhost"        Set the certificate's Common Name (CN).
#                              Kept for compatibility, although browsers verify
#                              hostnames using SAN instead.
# -addext "subjectAltName=..." Specify the hostnames and IP addresses covered
#                              by the certificate: localhost, 127.0.0.1
#                              (IPv4) and ::1 (IPv6).
#                              Without SAN, hostname verification fails even
#                              if the certificate is trusted.
secrets-certs: | secrets-dir
	@mkdir -p "$(CERTIFICATE_DIR)"
	@if [ -s "$(TLS_CERTIFICATE)" ] && [ -s "$(TLS_PRIVATE_KEY)" ]; then \
		printf "$(GREEN_COLOR)✓ $(TLS_CERTIFICATE) already exists, skipping 🔒$(DEFAULT_COLOR)\n"; \
	else \
		printf "$(YELLOW_COLOR)🔒 Generating a self-signed certificate for localhost...$(DEFAULT_COLOR)\n"; \
		openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
			-subj "/CN=localhost" \
			-addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1" \
			-keyout "$(TLS_PRIVATE_KEY)" -out "$(TLS_CERTIFICATE)" 2>/dev/null && \
		chmod 600 "$(TLS_PRIVATE_KEY)" && \
		printf "$(GREEN_COLOR)✓ $(TLS_CERTIFICATE) generated (self-signed)$(DEFAULT_COLOR)\n"; \
	fi
