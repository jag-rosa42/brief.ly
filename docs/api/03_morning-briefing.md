# Morning Briefing

A single endpoint returns everything the dashboard needs: one topic cluster per profile interest, each with its summary and its articles. The briefing is built on each request; nothing is precomputed. Conventions, tokens and errors are in [00_conventions.md](00_conventions.md).

Nothing is implemented yet: on `main`, Morning Briefing only has `/health`, and its API router still uses the old `/api` prefix (`srcs/services/morning-briefing/src/api/routers/__init__.py`).

| Kind | Method | Caller path | Service path | Auth | Success | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Frontend | GET | `/api/morning-briefing/briefing` | `/briefing` | Bearer | 200 | To do |
| Public | GET | `/public/v1/morning-briefing` | same | API key (`read`) | 200 | To do |
| Public | GET | `/public/v1/openapi/morning-briefing.json` | same | None | 200 | To do |
| Internal | GET | — | `/health` | None | 200 | Done |

The Public route answers like the Frontend route, plus `401 INVALID_API_KEY`, `403 INSUFFICIENT_SCOPE` and `429`, exactly like Personalization's Public routes. Its OpenAPI document is shown on `/public/v1/docs` (see [02_personalization.md](02_personalization.md)).

## Endpoint details

Each endpoint below shows the request and every possible response.

### GET /api/morning-briefing/briefing

Service path: `GET /briefing`. Public twin: `GET /public/v1/morning-briefing`.

How it is built:
1. `GET /internal/v1/me/profile` on Personalization, with the token Morning Briefing received (the user's data, so the user's token).
2. `GET /internal/v1/topics` and `GET /internal/v1/articles?topic_id=...` on Content Management, with Morning Briefing's service token (data that belongs to no user). Articles and topics carry their summaries; the article list excludes `rejected: true` articles (see [06_service-to-service.md](06_service-to-service.md#summaries-an-enrichment-pipeline)). The topic catalog still includes topics with no eligible articles.

Morning Briefing never calls AI Processing.

```text
Header: Authorization: Bearer <access token>

200 OK
{
  "profile": {
    "name": str,
    "topic_ids": [str],
    "saved_article_ids": [UUID]          [] when nothing saved
  },
  "topic_clusters": [
    {
      "topic_id": str,
      "summary": str | null,             null until AI Processing has summarized the topic
      "articles": [
        {
          "article_id": UUID,
          "title": str,
          "publisher_name": str,
          "url": str,
          "summary": str | null,         null until AI Processing has summarized the article
          "read_time_minutes": int,
          "topic_id": str
        }
      ]
    }
  ]
}
401 Unauthorized      TOKEN_EXPIRED is passed through from Personalization
404 Not Found         PROFILE_NOT_FOUND (frontend sends the user to onboarding)
503 Unavailable       SERVICE_UNAVAILABLE (Personalization or Content Management unreachable)
```
