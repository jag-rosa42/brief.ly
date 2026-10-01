here a tree of my monorepo:
tree -L 3
.
├── 1.md
├── compose.mac.yaml
├── compose.override.yaml
├── compose.yaml
├── docs
│   ├── adr
│   │   ├── 0000-use-adr-for-architectural-decision-tracking.md
│   │   ├── 0001-adopt-git-flow-branching-strategy.md
│   │   ├── 0002-use-rebase-over-merge-for-branch-integration.md
│   │   ├── 0003-adopt-commit-message-convention.md
│   │   ├── 0004-adopt-clean-architecture-for-backend-services-and-feature-based-architecture-for-frontend.md
│   │   └── template.md
│   ├── architecture
│   │   ├── 00_README.md
│   │   ├── 01_project-architecture.md
│   │   ├── 02_overview.md
│   │   ├── 03_service.md
│   │   ├── 04_backend-service-structure.md
│   │   └── 05_frontend-structure.md
│   ├── conventions
│   │   ├── commits.md
│   │   ├── git-conventions.md
│   │   ├── git-workflow.md
│   │   └── README.md
│   ├── resources.md
│   └── think
│       └── prompt.md
├── Makefile
├── README.dev.md
├── README.docker.md
├── README.md
├── shared
│   ├── mk
│   │   ├── colors.mk
│   │   ├── secrets.mk
│   │   └── service.mk
│   ├── packages
│   │   └── shared_errors
│   ├── script
│   │   └── start-databases.sh
│   ├── secrets
│   │   ├── jwt_private_key
│   │   ├── jwt_public_key
│   │   └── postgres_password
│   └── templates
│       ├── backend-service
│       └── README.md
├── srcs
│   ├── frontend
│   │   ├── conf
│   │   ├── DEV_DOC.md
│   │   ├── Dockerfile
│   │   ├── Dockerfile.dev
│   │   ├── eslint.config.js
│   │   ├── index.html
│   │   ├── Makefile
│   │   ├── node_modules
│   │   ├── package.json
│   │   ├── package-lock.json
│   │   ├── src
│   │   ├── tests
│   │   ├── tsconfig.app.json
│   │   ├── tsconfig.json
│   │   ├── tsconfig.node.json
│   │   ├── vite.config.ts
│   │   └── vitest.config.ts
│   └── services
│       ├── ai-processing
│       ├── content-management
│       ├── identity
│       ├── morning-briefing
│       └── personalization
└── transcendence.code-workspace


and a the identity service tree:
.
├── alembic.ini
├── Dockerfile
├── Dockerfile.dev
├── Makefile
├── migrations
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       ├── 61ee302d0e3a_add_refresh_tokens_table.py
│       └── 91d86b6061ad_add_account_table.py
├── pyproject.toml
├── README.md
├── settings_refactoring.md
├── src
│   ├── api
│   │   ├── dependencies
│   │   │   ├── account.py
│   │   │   ├── database.py
│   │   │   ├── __init__.py
│   │   │   └── security.py
│   │   ├── errors
│   │   │   ├── codes.py
│   │   │   ├── handlers.py
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── routers
│   │   │   ├── accounts
│   │   │   │   ├── __init__.py
│   │   │   │   └── router.py
│   │   │   ├── auth
│   │   │   │   ├── __init__.py
│   │   │   │   └── router.py
│   │   │   ├── health
│   │   │   │   ├── __init__.py
│   │   │   │   └── router.py
│   │   │   └── __init__.py
│   │   └── schemas
│   │       ├── account.py
│   │       ├── authentication.py
│   │       ├── __init__.py
│   │       └── session.py
│   ├── application
│   │   ├── __init__.py
│   │   ├── port
│   │   │   ├── __init__.py
│   │   │   ├── password_hasher.py
│   │   │   └── token
│   │   │       ├── __init__.py
│   │   │       ├── service.py
│   │   │       └── types.py
│   │   └── use_cases
│   │       ├── accounts
│   │       │   ├── get_current_account.py
│   │       │   └── __init__.py
│   │       ├── auth
│   │       │   ├── __init__.py
│   │       │   ├── login_account.py
│   │       │   ├── logout_account.py
│   │       │   └── register_account.py
│   │       ├── __init__.py
│   │       └── session
│   │           ├── account_session.py
│   │           ├── create_account_session.py
│   │           ├── __init__.py
│   │           ├── refresh_account_session.py
│   │           └── refresh_token_validator.py
│   ├── domain
│   │   ├── entities
│   │   │   ├── account.py
│   │   │   ├── __init__.py
│   │   │   └── refresh_token.py
│   │   ├── exception.py
│   │   ├── __init__.py
│   │   ├── repositories
│   │   │   ├── account_repository.py
│   │   │   ├── __init__.py
│   │   │   └── refresh_token_repository.py
│   │   └── value_objects
│   │       ├── email.py
│   │       ├── __init__.py
│   │       └── password_hash.py
│   ├── infrastructure
│   │   ├── database
│   │   │   ├── bootstrap.py
│   │   │   ├── config
│   │   │   │   ├── engine.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── migration_status.py
│   │   │   │   ├── session.py
│   │   │   │   └── settings.py
│   │   │   ├── __init__.py
│   │   │   ├── models
│   │   │   │   ├── account.py
│   │   │   │   ├── base.py
│   │   │   │   ├── __init__.py
│   │   │   │   └── refresh_token.py
│   │   │   └── repositories
│   │   │       ├── __init__.py
│   │   │       ├── sqlalchemy_account_repository.py
│   │   │       └── sqlalchemy_refresh_token_repository.py
│   │   ├── __init__.py
│   │   └── security
│   │       ├── __init__.py
│   │       ├── password_hasher.py
│   │       └── token
│   │           ├── __init__.py
│   │           ├── jwt_payload.py
│   │           ├── token_service.py
│   │           └── token_type.py
│   ├── __init__.py
│   └── main.py
├── test_decoupling.md
├── tests
│   ├── conftest.py
│   ├── e2e
│   │   ├── accounts
│   │   │   └── test_account_endpoint.py
│   │   └── auth
│   │       ├── test_login_endpoint.py
│   │       ├── test_register_endpoint.py
│   │       └── test_session_flow.py
│   ├── fixtures
│   │   ├── accounts.py
│   │   ├── database.py
│   │   ├── factory.py
│   │   ├── http.py
│   │   ├── __init__.py
│   │   ├── security.py
│   │   └── sessions.py
│   ├── __init__.py
│   ├── integration
│   │   ├── api
│   │   │   ├── auth
│   │   │   │   ├── test_login_router.py
│   │   │   │   ├── test_logout_router.py
│   │   │   │   ├── test_refresh_router.py
│   │   │   │   └── test_register_router.py
│   │   │   ├── test_account_router.py
│   │   │   └── test_health_endpoint.py
│   │   └── repositories
│   │       ├── test_sqlalchemy_account_repository.py
│   │       └── test_sqlalchemy_refresh_token_repository.py
│   └── unit
│       ├── api
│       │   ├── test_get_db.py
│       │   └── test_health.py
│       ├── application
│       │   ├── test_create_account_session.py
│       │   ├── test_login_account.py
│       │   ├── test_logout_account.py
│       │   ├── test_refresh_account_session.py
│       │   ├── test_refresh_token_validator.py
│       │   └── test_register_account.py
│       ├── domain
│       │   ├── entities
│       │   │   ├── test_account.py
│       │   │   └── test_refresh_token.py
│       │   └── value_objects
│       │       ├── test_email.py
│       │       └── test_password_hash.py
│       └── infrastructure
│           ├── database
│           │   ├── test_engine.py
│           │   ├── test_session.py
│           │   └── test_settings.py
│           └── security
│               ├── test_password_hasher.py
│               └── test_token_service.py
└── uv.lock


More context about our choices:
- the frontend is done with ReactJS/TS, no idea how the token will be stored and serve
- microservices backend
- No WAF/Modsecurity + Vault
- No Websocket plan so far
- Will add grafana + prometheus
- No queue or worked system is planned so far or background job, just a CRON plan on the content-management service
- There is no users role plan so far
- so far, Content Management will act as purely data provider and we designing endpoint so that AI processing service can fetch the data
- No online deployment plan yet but we are coding with that in mind so that we have the minimum amount of change to be done later

here my compose.yaml + compose.override.yaml:

#compose.yaml
name: "${DOMAIN}"

# ==============================================================================
# One-shot bootstrap: apply this service's migrations before the service starts.
# ==============================================================================

x-backend-prestart: &backend-prestart
  pull_policy: build
  restart: "no"
  profiles: [backend]
  environment:
    POSTGRES_HOST: pgsql
    POSTGRES_USER: ${POSTGRES_USER:?Variable not set}
    POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    POSTGRES_DEFAULT_DB_NAME: ${POSTGRES_DEFAULT_DB_NAME:?Variable not set}
  command:
    ["sh", "-c", "python -m src.infrastructure.database.bootstrap && alembic upgrade head"]
  secrets:
    - postgres_password
  depends_on:
    pgsql:
      condition: service_healthy

# ==============================================================================
# The service's backend container
# ==============================================================================

x-backend-service: &backend-service
  pull_policy: build
  restart: "always"
  profiles: [backend]
  environment:
    POSTGRES_HOST: pgsql
    POSTGRES_USER: ${POSTGRES_USER:?Variable not set}
    POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    POSTGRES_DEFAULT_DB_NAME: ${POSTGRES_DEFAULT_DB_NAME:?Variable not set}

  secrets:
    - postgres_password
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
    interval: 10s
    timeout: 5s
    retries: 5

# ==============================================================================
# Reusable each service's image build
# ==============================================================================

# Ai-processing
x-ai-processing-image-build: &ai-processing-image-build
  container_name: ai-processing
  build:
    context: ./srcs/services/ai-processing
    dockerfile: Dockerfile
    additional_contexts:
      shared_errors: ./shared/packages/shared_errors
  image: ai-processing
  env_file:
    - ./srcs/services/ai-processing/.env

# Content-management
x-content-management-image-build: &content-management-image-build
  container_name: content-management
  build:
    context: ./srcs/services/content-management
    dockerfile: Dockerfile
    additional_contexts:
      shared_errors: ./shared/packages/shared_errors
  image: content-management
  env_file:
    - ./srcs/services/content-management/.env

# Identity
x-identity-image-build: &identity-image-build
  container_name: identity
  build:
    context: ./srcs/services/identity
    dockerfile: Dockerfile
    additional_contexts:
      shared_errors: ./shared/packages/shared_errors
  image: identity
  env_file:
    - ./srcs/services/identity/.env

# Morning-briefing
x-morning-briefing-image-build: &morning-briefing-image-build
  container_name: morning-briefing
  build:
    context: ./srcs/services/morning-briefing
    dockerfile: Dockerfile
    additional_contexts:
      shared_errors: ./shared/packages/shared_errors
  image: morning-briefing
  env_file:
    - ./srcs/services/morning-briefing/.env

# Personalization
x-personalization-image-build: &personalization-image-build
  container_name: personalization
  build:
    context: ./srcs/services/personalization
    dockerfile: Dockerfile
    additional_contexts:
      shared_errors: ./shared/packages/shared_errors
  image: personalization
  env_file:
    - ./srcs/services/personalization/.env


# ==============================================================================
# Services
# ==============================================================================

services:
  # FRONTEND
  frontend:
    build:
      context: ./srcs/frontend/
      dockerfile: Dockerfile
    image: front-react-ts
    container_name: frontend
    pull_policy: build
    ports:
      - 8080:${FRONTEND_PORT:?Variable not set}
    profiles:
      - frontend

  # REVERSE PROXY

  # API_GATEWAY

  # DATABASES
  pgsql:
    image: docker.io/library/postgres:18
    container_name: pgsql
    restart: "always"
    profiles:
      - databases
    healthcheck:
      test: ["CMD-SHELL", 'pg_isready -U "$$POSTGRES_USER" -d postgres']
      interval: 10s
      retries: 5
      start_period: 30s
      timeout: 10s
    volumes:
      - pgsql:${PGDATA:?Variable not set}
    environment:
      PGDATA: ${PGDATA:?Variable not set}
      POSTGRES_USER: ${POSTGRES_USER:?Variable not set}
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      POSTGRES_DB: ${POSTGRES_DEFAULT_DB_NAME:?Variable not set}
    secrets:
      - postgres_password

  pgvector:
    image: docker.io/pgvector/pgvector:pg18
    container_name: pgvector
    restart: "always"
    profiles:
      - databases
    healthcheck:
      test: ["CMD-SHELL", 'pg_isready -U "$$POSTGRES_USER" -d postgres']
      interval: 10s
      retries: 5
      start_period: 30s
      timeout: 10s
    volumes:
      - pgvector:${PGDATA:?Variable not set}
    environment:
      PGDATA: ${PGDATA:?Variable not set}
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      POSTGRES_USER: ${POSTGRES_USER:?Variable not set}
      POSTGRES_DB: ${POSTGRES_DEFAULT_DB_NAME:?Variable not set}
    secrets:
      - postgres_password

  # BACKEND

  # Ai-processing
  prestart-ai-processing:
    <<: [*ai-processing-image-build, *backend-prestart]
    environment:
      POSTGRES_HOST: pgvector
      POSTGRES_USER: ${POSTGRES_USER:?Variable not set}
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      POSTGRES_DEFAULT_DB_NAME: ${POSTGRES_DEFAULT_DB_NAME:?Variable not set}
    depends_on:
      pgvector:
        condition: service_healthy
    container_name: prestart-ai-processing

  ai-processing:
    <<: [*ai-processing-image-build, *backend-service]
    depends_on:
      pgvector:
        condition: service_healthy
      prestart-ai-processing:
        condition: service_completed_successfully

  # Content-management
  prestart-content-management:
    <<: [*content-management-image-build, *backend-prestart]
    container_name: prestart-content-management

  content-management:
    <<: [*content-management-image-build, *backend-service]
    depends_on:
      pgsql:
        condition: service_healthy
      prestart-content-management:
        condition: service_completed_successfully

  # Identity
  prestart-identity:
    <<: [*identity-image-build, *backend-prestart]
    container_name: prestart-identity
    environment:
      POSTGRES_HOST: pgsql
      POSTGRES_USER: ${POSTGRES_USER:?Variable not set}
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      POSTGRES_DEFAULT_DB_NAME: ${POSTGRES_DEFAULT_DB_NAME:?Variable not set}
      JWT_PRIVATE_KEY_FILE: /run/secrets/jwt_private_key
      JWT_PUBLIC_KEY_FILE: /run/secrets/jwt_public_key
    secrets:
      - jwt_private_key
      - jwt_public_key
      - postgres_password

  identity:
    <<: [*identity-image-build, *backend-service]
    depends_on:
      pgsql:
        condition: service_healthy
      prestart-identity:
        condition: service_completed_successfully
    environment:
      POSTGRES_HOST: pgsql
      POSTGRES_USER: ${POSTGRES_USER:?Variable not set}
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      POSTGRES_DEFAULT_DB_NAME: ${POSTGRES_DEFAULT_DB_NAME:?Variable not set}
      JWT_PRIVATE_KEY_FILE: /run/secrets/jwt_private_key
      JWT_PUBLIC_KEY_FILE: /run/secrets/jwt_public_key
    secrets:
      - jwt_private_key
      - jwt_public_key
      - postgres_password

  # Morning-briefing
  prestart-morning-briefing:
    <<: [*morning-briefing-image-build, *backend-prestart]
    container_name: prestart-morning-briefing

  morning-briefing:
    <<: [*morning-briefing-image-build, *backend-service]
    depends_on:
      pgsql:
        condition: service_healthy
      prestart-morning-briefing:
        condition: service_completed_successfully

  # Personalization
  prestart-personalization:
    <<: [*personalization-image-build, *backend-prestart]
    container_name: prestart-personalization

  personalization:
    <<: [*personalization-image-build, *backend-service]
    depends_on:
      pgsql:
        condition: service_healthy
      prestart-personalization:
        condition: service_completed_successfully


  # ADMINISTRATION

secrets:
  postgres_password:
    file: ./shared/secrets/postgres_password
  jwt_private_key:
    file: ./shared/secrets/jwt_private_key
  jwt_public_key:
    file: ./shared/secrets/jwt_public_key

volumes:
  pgsql:
  pgvector:

networks:
  default:
    name: ${DOMAIN}
    driver: bridge

#compose.override.yaml
# ==============================================================================
# Reusable each service's image build
# ==============================================================================

# Ai-processing
x-ai-processing-dev-image-build: &ai-processing-dev-image-build
  build:
    dockerfile: Dockerfile.dev
  volumes:
    - ./srcs/services/ai-processing:/app/srcs/services/ai-processing:Z
    - ./shared/packages/shared_errors:/app/shared/packages/shared_errors:Z

# Content-management
x-content-management-dev-image-build: &content-management-dev-image-build
  build:
    dockerfile: Dockerfile.dev
  volumes:
    - ./srcs/services/content-management:/app/srcs/services/content-management:Z
    - ./shared/packages/shared_errors:/app/shared/packages/shared_errors:Z

# Identity
x-identity-dev-image-build: &identity-dev-image-build
  build:
    dockerfile: Dockerfile.dev
  volumes:
    - ./srcs/services/identity:/app/srcs/services/identity:Z
    - ./shared/packages/shared_errors:/app/shared/packages/shared_errors:Z

# Morning-briefing
x-morning-briefing-dev-image-build: &morning-briefing-dev-image-build
  build:
    dockerfile: Dockerfile.dev
  volumes:
    - ./srcs/services/morning-briefing:/app/srcs/services/morning-briefing:Z
    - ./shared/packages/shared_errors:/app/shared/packages/shared_errors:Z

# Personalization
x-personalization-dev-image-build: &personalization-dev-image-build
  build:
    dockerfile: Dockerfile.dev
  volumes:
    - ./srcs/services/personalization:/app/srcs/services/personalization:Z
    - ./shared/packages/shared_errors:/app/shared/packages/shared_errors:Z


# ==============================================================================
#      Services
# ==============================================================================

services:
  frontend:
    build:
      context: ./srcs/frontend/
      dockerfile: Dockerfile.dev
    image: front-react-ts
    container_name: frontend-dev
    pull_policy: build
    ports:
      - "${FRONTEND_PORT:?Variable not set}:5173"
    volumes:
      - ./srcs/frontend/:/app:Z # :Z is important on Fedora/SELinux.
      - frontend_node_modules:/app/node_modules
    environment:
      VITE_USE_POLLING: ${VITE_USE_POLLING:-false}
      VITE_HMR_HOST: localhost
      VITE_HMR_CLIENT_PORT: ${FRONTEND_PORT:?Variable not set}

  front-test:
    build:
      context: ./srcs/frontend/
      dockerfile: Dockerfile.dev
    volumes:
      - ./srcs/frontend/:/app:Z # :Z is important on Fedora/SELinux.
      - frontend_node_modules:/app/node_modules
    command: ["npm", "run", "test", "--", "--watch"]
    profiles:
      - front-test

  adminer:
    image: docker.io/library/adminer:6.1.1
    container_name: adminer
    restart: "no"
    depends_on:
      pgsql:
        condition: service_healthy
      pgvector:
        condition: service_healthy
    environment:
      ADMINER_DESIGN: pepa-linha-dark
    ports:
      - "${ADMINER_PORT:?Variable not set}:8080"
    profiles:
      - databases

  pgsql:
    restart: "no"
    ports:
      - "${POSTGRES_PORT:?Variable not set}:5432"

  pgvector:
    restart: "no"
    ports:
      - "${AI_POSTGRES_PORT:?Variable not set}:5432"


  # Ai-processing
  prestart-ai-processing:
    <<: *ai-processing-dev-image-build

  ai-processing:
    <<: *ai-processing-dev-image-build
    ports:
      - "${AI_PROCESSING_PORT:?Variable not set}:${SERVICE_CONTAINER_PORT:?Variable not set}"
    environment:
      POSTGRES_HOST: pgvector
      # Used by Uvicorn/watchfiles for backend --reload, independently of Vite.
      WATCHFILES_FORCE_POLLING: ${WATCHFILES_FORCE_POLLING:-false}

  # Content-management
  prestart-content-management:
    <<: *content-management-dev-image-build

  content-management:
    <<: *content-management-dev-image-build
    ports:
      - "${CONTENT_MANAGEMENT_PORT:?Variable not set}:${SERVICE_CONTAINER_PORT:?Variable not set}"
    environment:
      # Used by Uvicorn/watchfiles for backend --reload, independently of Vite.
      WATCHFILES_FORCE_POLLING: ${WATCHFILES_FORCE_POLLING:-false}

  # Identity
  prestart-identity:
    <<: *identity-dev-image-build

  identity:
    <<: *identity-dev-image-build
    ports:
      - "${IDENTITY_PORT:?Variable not set}:${SERVICE_CONTAINER_PORT:?Variable not set}"
    environment:
      # Used by Uvicorn/watchfiles for backend --reload, independently of Vite.
      WATCHFILES_FORCE_POLLING: ${WATCHFILES_FORCE_POLLING:-false}

  # Morning-briefing
  prestart-morning-briefing:
    <<: *morning-briefing-dev-image-build

  morning-briefing:
    <<: *morning-briefing-dev-image-build
    ports:
      - "${MORNING_BRIEFING_PORT:?Variable not set}:${SERVICE_CONTAINER_PORT:?Variable not set}"
    environment:
      # Used by Uvicorn/watchfiles for backend --reload, independently of Vite.
      WATCHFILES_FORCE_POLLING: ${WATCHFILES_FORCE_POLLING:-false}

  # Personalization
  prestart-personalization:
    <<: *personalization-dev-image-build

  personalization:
    <<: *personalization-dev-image-build
    ports:
      - "${PERSONALIZATION_PORT:?Variable not set}:${SERVICE_CONTAINER_PORT:?Variable not set}"
    environment:
      # Used by Uvicorn/watchfiles for backend --reload, independently of Vite.
      WATCHFILES_FORCE_POLLING: ${WATCHFILES_FORCE_POLLING:-false}

volumes:
  frontend_node_modules:


my identity service:

i am using this from fastapi

bearer_token_scheme = HTTPBearer()

AccessTokenDep = Annotated[HTTPAuthorizationCredentials, Depends(bearer_token_scheme)]



and my claims are structured thought this class:
class JWTTokenPayload(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_alias=True,
    )
    token_id: str = Field(alias="jti")
    subject: str = Field(alias="sub")
    token_type: TokenType = Field(alias="type")
    issued_at: int = Field(alias="iat")
    expires_at: int = Field(alias="exp")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> JWTTokenPayload:
        try:
            return cls.model_validate(payload)
        except ValidationError as exc:
            raise InvalidTokenError() from exc


and i use this lib: pyjwt[crypto]>=2.14.0"


here my full implementation:


class JWTTokenService:
    def __init__(self):
        self._private_key: SecretStr = settings.JWT_PRIVATE_KEY
        self._public_key: str = settings.JWT_PUBLIC_KEY
        self._algorithm: str = settings.JWT_ALGORITHM
        self._access_token_lifetime: timedelta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self._refresh_token_lifetime: timedelta = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    def create_access_token(self, account_id: UUID) -> str:
        created_token: CreatedToken = self._create_token(
            account_id,
            token_type=TokenType.ACCESS,
        )
        return created_token.token

    def verify_access_token(self, token: str) -> AccessTokenClaims:
        payload: JWTTokenPayload = self._decode(token, expected_type=TokenType.ACCESS)

        account_id: UUID = self._parse_uuid(payload.subject)
        return AccessTokenClaims(
            account_id=account_id,
            expires_at=datetime.fromtimestamp(timestamp=payload.expires_at, tz=UTC),
        )

    def create_refresh_token(self, account_id: UUID) -> CreatedRefreshToken:
        refresh_token: CreatedToken = self._create_token(
            account_id,
            token_type=TokenType.REFRESH,
        )
        return CreatedRefreshToken(
            id=refresh_token.id,
            token=refresh_token.token,
            token_hash=self.hash_token(refresh_token.token),
            expires_at=refresh_token.expires_at,
        )

    def verify_refresh_token(self, token: str) -> RefreshTokenClaims:
        payload: JWTTokenPayload = self._decode(token, expected_type=TokenType.REFRESH)

        token_id: UUID = self._parse_uuid(payload.token_id)
        account_id: UUID = self._parse_uuid(payload.subject)

        return RefreshTokenClaims(
            id=token_id,
            account_id=account_id,
            expires_at=datetime.fromtimestamp(timestamp=payload.expires_at, tz=UTC),
        )

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _create_token(self, account_id: UUID, token_type: TokenType) -> CreatedToken:
        now: datetime = datetime.now(UTC)
        token_id: UUID = uuid4()
        lifetime: timedelta = (
            self._access_token_lifetime
            if token_type == TokenType.ACCESS
            else self._refresh_token_lifetime
        )
        expires_at: datetime = now + lifetime
        payload: dict[str, Any] = {
            "jti": str(token_id),  # subject
            "sub": str(account_id),  # subject
            "type": token_type,
            "iat": now,  # Issued at
            "exp": expires_at,
        }
        token: str = jwt.encode(
            payload,
            self._private_key.get_secret_value(),
            self._algorithm,
        )
        return CreatedToken(id=token_id, token=token, expires_at=expires_at)

    def _decode(self, token: str, expected_type: TokenType) -> JWTTokenPayload:
        try:
            payload: dict[str, Any] = jwt.decode(
                jwt=token,
                key=self._public_key,
                algorithms=[self._algorithm],
                options={"require": ["sub", "type", "iat", "exp"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError() from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError() from exc

        jwt_payload: JWTTokenPayload = JWTTokenPayload.from_dict(payload)
        if jwt_payload.token_type != expected_type:
            logger.debug("Unexpected token type: expected=%s", expected_type.value)
            raise InvalidTokenError()
        return jwt_payload

    def _parse_uuid(self, value: str) -> UUID:
        try:
            return UUID(value)
        except ValueError as exc:
            raise InvalidTokenError() from exc


class CreateAccountSession:
    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
    ) -> None:
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository
        self._token_service: TokenService = token_service

    def execute(self, account_id: UUID) -> AccountSession:
        access_token: str = self._token_service.create_access_token(account_id)
        created_refresh_token: CreatedRefreshToken = (
            self._token_service.create_refresh_token(account_id)
        )
        refresh_token = RefreshToken(
            id=created_refresh_token.id,
            account_id=account_id,
            token_hash=created_refresh_token.token_hash,
            expires_at=created_refresh_token.expires_at,
            created_at=datetime.now(UTC),
        )

        self._refresh_token_repository.add(refresh_token)

        return AccountSession(
            access_token=access_token,
            refresh_token=created_refresh_token.token,
            refresh_token_id=created_refresh_token.id,
        )

class RefreshAccountSession:
    def __init__(
        self,
        refresh_token_validator: RefreshTokenValidator,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
        create_account_session: CreateAccountSession,
    ) -> None:
        self._refresh_token_validator = refresh_token_validator
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository
        self._token_service: TokenService = token_service
        self._create_account_session: CreateAccountSession = create_account_session

    def execute(self, refresh_token: str) -> AccountSession:
        current_refresh_token = self._refresh_token_validator.get_valid_refresh_token(
            refresh_token
        )
        now: datetime = datetime.now(UTC)
        self._validate_refresh_token_state(current_refresh_token, now)
        new_account_session: AccountSession = self._create_account_session.execute(
            current_refresh_token.account_id
        )

        self._refresh_token_repository.flush()

        self._rotate_refresh_token(
            current_refresh_token=current_refresh_token,
            new_refresh_token_id=new_account_session.refresh_token_id,
            now=now,
        )
        self._refresh_token_repository.commit()

        return new_account_session

    def _validate_refresh_token_state(
        self,
        refresh_token: RefreshToken,
        now: datetime,
    ) -> None:
        if refresh_token.is_revoked():
            if refresh_token.was_rotated():
                self._refresh_token_repository.revoke_all_for_account(
                    refresh_token.account_id,
                    now,
                )
                self._refresh_token_repository.commit()
            raise TokenRevokedError()
        if refresh_token.is_expired(now):
            raise TokenExpiredError()

    def _rotate_refresh_token(
        self,
        current_refresh_token: RefreshToken,
        new_refresh_token_id: UUID,
        now: datetime,
    ) -> None:
        current_refresh_token.revoke(now, replaced_by=new_refresh_token_id)
        self._refresh_token_repository.update(current_refresh_token)

class RefreshTokenValidator:
    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
    ) -> None:
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository
        self._token_service: TokenService = token_service

    def get_valid_refresh_token(self, refresh_token: str) -> RefreshToken:
                # Verify the JWT signature, claims, token type, etc.
        claims: RefreshTokenClaims = self._token_service.verify_refresh_token(
            refresh_token
        )

        # Find the database record corresponding to the JWT's `jti`.
        stored_token: RefreshToken | None = self._refresh_token_repository.find_by_id(
            claims.id,
        )

        # The database stores only the hash of the refresh token.
        # Hash the presented token and compare it with the stored hash.
        if (
            stored_token is None
            or stored_token.token_hash != self._token_service.hash_token(refresh_token)
        ):
            raise InvalidTokenError()
        return stored_token

class LoginAccount:
    def __init__(
        self,
        account_repository: AccountRepository,
        password_hasher: PasswordHasher,
        create_account_session: CreateAccountSession,
    ) -> None:
        self._account_repository: AccountRepository = account_repository
        self._password_hasher: PasswordHasher = password_hasher
        self._create_account_session: CreateAccountSession = create_account_session

    def execute(self, email: str, password: str) -> AccountSession:
        account: Account | None = self._account_repository.find_by_email(Email(email))
        if account is None:
            raise InvalidCredentialsError()
        if not self._password_hasher.verify(password, account.password_hash):
            raise InvalidCredentialsError()

        session: AccountSession = self._create_account_session.execute(account.id)
        self._account_repository.commit()

        return session

class LogoutAccount:
    def __init__(
        self,
        refresh_token_validator: RefreshTokenValidator,
        refresh_token_repository: RefreshTokenRepository,
    ) -> None:
        self._refresh_token_validator: RefreshTokenValidator = refresh_token_validator
        self._refresh_token_repository: RefreshTokenRepository = refresh_token_repository

    def execute(self, refresh_token: str) -> None:
        try:
            stored: RefreshToken = self._refresh_token_validator.get_valid_refresh_token(
                refresh_token
            )
        except (InvalidTokenError, TokenExpiredError):
            return

        if stored.is_revoked():
            return

        stored.revoke(datetime.now(UTC))
        self._refresh_token_repository.update(stored)
        self._refresh_token_repository.commit()


class RegisterAccount:
    def __init__(
        self,
        account_repository: AccountRepository,
        password_hasher: PasswordHasher,
        create_account_session: CreateAccountSession,
    ) -> None:
        self._account_repository: AccountRepository = account_repository
        self._password_hasher: PasswordHasher = password_hasher
        self._create_account_session: CreateAccountSession = create_account_session

    def execute(self, email: str, password: str) -> AccountSession:
        email_value_object: Email = Email(email)

        existing_account: Account | None = self._account_repository.find_by_email(
            email_value_object
        )

        if existing_account is not None:
            raise EmailAlreadyRegisteredError()

        password_hash: PasswordHash = self._password_hasher.hash(password)

        account: Account = Account(
            id=uuid4(),
            email=email_value_object,
            password_hash=password_hash,
            created_at=datetime.datetime.now(datetime.UTC),
        )
        # TODO: Revisit the transaction boundary.
        # Currently, this use case explicitly commits/rolls back through the repository.
        # Consider moving transaction management to a Unit of Work or outer application
        # boundary so the entire use case is executed within a single transaction.
        try:
            self._account_repository.save(account)
            session: AccountSession = self._create_account_session.execute(account.id)
            self._account_repository.commit()
        except IntegrityError as exc:
            self._account_repository.rollback()
            raise EmailAlreadyRegisteredError() from exc
        except Exception:
            self._account_repository.rollback()
            raise

        return session

class GetCurrentAccount:
    def __init__(
        self,
        account_repository: AccountRepository,
        token_service: TokenService,
    ) -> None:
        self._accounts: AccountRepository = account_repository
        self._token_service: TokenService = token_service

    def execute(self, access_token: str) -> Account:
        claims: AccessTokenClaims = self._token_service.verify_access_token(
            access_token
        )
        account: Account | None = self._accounts.find_by_id(
            claims.account_id
        )
        if account is None:
            raise InvalidTokenError()
        return account


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AccountSessionResponse,
)
def register(
    body: RegisterRequest,
    register_account: RegisterAccountDep,
) -> AccountSessionResponse:
    session: AccountSession = register_account.execute(
        email=body.email, password=body.password.get_secret_value()
    )
    return AccountSessionResponse.from_session(session)


@router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=AccountSessionResponse,
)
def login(
    body: LoginRequest,
    login_account: LoginAccountDep,
) -> AccountSessionResponse:
    session: AccountSession = login_account.execute(
        email=body.email,
        password=body.password.get_secret_value(),
    )
    return AccountSessionResponse.from_session(session)


@router.post(
    path="/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    body: LogoutRequest,
    logout_account: LogoutAccountDep,
) -> None:
    logout_account.execute(body.refresh_token)


@router.post(
    path="/refresh",
    status_code=status.HTTP_200_OK,
    response_model=AccountSessionResponse,
)
def refresh(
    body: RefreshRequest,
    refresh_account_session: RefreshAccountSessionDep,
) -> AccountSessionResponse:
    session: AccountSession = refresh_account_session.execute(body.refresh_token)
    return AccountSessionResponse.from_session(session)


router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)


@router.get(
    path="/me",
    status_code=status.HTTP_200_OK,
    response_model=AccountResponse,
)
def get_me(current_account: CurrentAccountDep) -> AccountResponse:
    return AccountResponse.from_domain(current_account)
