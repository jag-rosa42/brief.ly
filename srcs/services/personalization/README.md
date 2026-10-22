# Personalization Service

Stores user profiles and the topics each user follows.

## Configuration

Service-specific variables, read from this service's `.env` (see `.env.example`):

| Variable | Description | Example |
| --- | --- | --- |
| `PROJECT_NAME` | Name of the service | `personalization` |
| `POSTGRES_DB_NAME` | Database of the service | `personalization_db` |
| `BACKEND_CORS_ORIGINS` | Origins allowed to call the API from a browser | `["http://localhost:5173"]` |
| `CONTENT_MANAGEMENT_URL` | Base URL of Content Management, used to fetch the topic catalog | `http://localhost:8083` (local), `http://content-management:8000` (containers) |

Shared database settings (`POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`) come from the root `.env`.
