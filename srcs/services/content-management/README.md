# Content Management Service

Content Management discovers and normalizes articles and exposes the internal
topic and ingestion APIs.

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

The file is ignored by Git. Add the credential before running `make ingest`,
which rejects a missing, unreadable, or empty file. Other Content Management
endpoints and services can run without a NewsAPI credential.
