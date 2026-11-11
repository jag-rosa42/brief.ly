# Content Management Service

Content Management discovers and normalizes articles and exposes the internal
topic and ingestion APIs.

## Service tokens

The `/internal/v1` routes (except `POST /ingestion-runs`) check the caller's
service token and its scope (ADR-0008, `docs/api/04_content-management.md`).

| Setting | Description | Example |
| --- | --- | --- |
| `JWT_SERVICE_AUDIENCE` (`.env`) | Audience of this service in service tokens | `transcendence:content-management` |
| `jwt_public_key` (secret file) | Identity's public key, to verify tokens, created by `make secrets` | `shared/secrets/jwt_public_key` (local), `/run/secrets/jwt_public_key` (containers) |

## NewsAPI credential

Article ingestion reads its NewsAPI credential from the repository-level secret
`shared/secrets/news_api_key` during local development and from
`/run/secrets/news_api_key` in containers. Do not put the key in this service's
`.env` file.

Host workflows create an empty file with restrictive permissions so the service
can start without a configured provider. To create it manually, run:

```bash
install -m 600 /dev/null shared/secrets/news_api_key
```

The file is ignored by Git. Add the credential before triggering ingestion.
Other Content Management endpoints and services can run without a NewsAPI
credential.

From the repository root, use `make ingest` when Content Management runs locally
on port 8083, `make ingest-docker` when it runs in host Docker, or `make ingest-vm`
when it runs in an already running VM. The VM command synchronizes the project
before calling the container; it does not start the VM or Content Management.

All three commands use the same HTTP client. It checks the key file where it
runs, reports HTTP and connection errors, and warns when ingestion succeeds only
partially. Requests time out after 10 minutes; a timed-out request may continue
running in Content Management, so check its logs before retrying.
