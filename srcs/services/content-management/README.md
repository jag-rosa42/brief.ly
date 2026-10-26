# Content Management Service

Content Management discovers and normalizes articles and exposes the internal
topic and ingestion APIs.

## NewsAPI credential

Article ingestion reads its NewsAPI credential from the repository-level secret
`shared/secrets/news_api_key` during local development and from
`/run/secrets/news_api_key` in containers. Do not put the key in this service's
`.env` file.

From the repository root, create the file with restrictive permissions, then
open it in an editor and add the credential:

```bash
install -m 600 /dev/null shared/secrets/news_api_key
```

The file is ignored by Git. It is required when Content Management is started,
but not for database-only or unrelated-service workflows.
