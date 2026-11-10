# Personalization Service

Stores user profiles and the topics each user follows.

## Configuration

Service-specific variables, read from this service's `.env` (see `.env.example`):

| Variable | Description | Example |
| --- | --- | --- |
| `PROJECT_NAME` | Name of the service | `personalization` |
| `POSTGRES_DB_NAME` | Database of the service | `personalization_db` |
| `BACKEND_CORS_ORIGINS` | Origins allowed to call the API from another origin (CORS) | `[]`: the browser uses the page's own origin (gateway or Vite proxy) |
| `CONTENT_MANAGEMENT_URL` | Base URL of Content Management, used to fetch the topic catalog | `http://localhost:8083` (local), `http://content-management:8000` (containers) |
| `IDENTITY_URL` | Base URL of Identity, which gives the service token for Content Management | `http://localhost:8081` (local), `http://identity:8000` (containers) |
| `JWT_SERVICE_AUDIENCE` | Audience of this service in service tokens | `transcendence:personalization` |
| `JWT_PUBLIC_API_AUDIENCE` | Audience of public API tokens, forwarded by Morning Briefing | `transcendence:public-api` |

Shared database settings (`POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`) come from the root `.env`.

Secrets, one file each (created by `make secrets`):

| Secret | Description | Local file | In containers |
| --- | --- | --- | --- |
| `jwt_public_key` | Identity's public key, to verify tokens | `shared/secrets/jwt_public_key` | `/run/secrets/jwt_public_key` |
| `personalization_client_secret` | This service's client secret at Identity, to get a service token (ADR-0008) | `shared/secrets/services/personalization_client_secret` | `/run/secrets/personalization_client_secret` |
