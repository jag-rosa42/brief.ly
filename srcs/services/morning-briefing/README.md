# Morning Briefing Service

Builds the user's briefing: their topics (from Personalization) with the topic summaries and articles (from Content Management).

## Configuration

Service-specific variables, read from this service's `.env` (see `.env.example`):

| Variable | Description | Example |
| --- | --- | --- |
| `PROJECT_NAME` | Name of the service | `morning_briefing` |
| `POSTGRES_DB_NAME` | Database of the service | `morning_briefing_db` |
| `BACKEND_CORS_ORIGINS` | Origins allowed to call the API from another origin (CORS) | `[]`: the browser uses the page's own origin (gateway or Vite proxy) |
| `CONTENT_MANAGEMENT_URL` | Base URL of Content Management, for the topics and articles | `http://localhost:8083` (local), `http://content-management:8000` (containers) |
| `PERSONALIZATION_URL` | Base URL of Personalization, for the user's profile | `http://localhost:8082` (local), `http://personalization:8000` (containers) |
| `IDENTITY_URL` | Base URL of Identity, which gives the service token for Content Management | `http://localhost:8081` (local), `http://identity:8000` (containers) |
| `JWT_SERVICE_AUDIENCE` | Audience of this service in service tokens | `transcendence:morning-briefing` |
| `JWT_PUBLIC_API_AUDIENCE` | Audience of public API tokens | `transcendence:public-api` |

Shared database settings (`POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`) come from the root `.env`.

Secrets, one file each (created by `make secrets`):

| Secret | Description | Local file | In containers |
| --- | --- | --- | --- |
| `jwt_public_key` | Identity's public key, to verify tokens | `shared/secrets/jwt_public_key` | `/run/secrets/jwt_public_key` |
| `morning_briefing_client_secret` | This service's client secret at Identity, to get a service token (ADR-0008) | `shared/secrets/services/morning_briefing_client_secret` | `/run/secrets/morning_briefing_client_secret` |
